"""Private direct messages. All lookups are scoped to the two participants."""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts import security
from accounts.account_views import ProtectedView, locked_user, validated
from accounts.community_catalog import page_data, query_value
from accounts.connected_accounts import connected_accounts
from accounts.models import User, username_key
from accounts.serializers import StrictSerializer
from accounts.views import RateLimited
from moderation.services import enabled, profile_visible
from .models import Conversation, Message


def throttle(request, scope='direct-read', limit=120):
    if security.count(scope, str(request.user.pk), ttl=60) > limit:
        raise RateLimited()


def require_sender(user):
    if not enabled(user):
        raise PermissionDenied({'detail': 'Hesap kullanılamıyor.', 'code': 'account_suspended'})
    if not user.email_verified:
        raise PermissionDenied({'detail': 'Önce e-posta adresinizi doğrulayın.', 'code': 'email_verification_required'})


def conversations_for(user):
    return Conversation.objects.filter(Q(lower_user=user) | Q(higher_user=user)).select_related('lower_user', 'higher_user')


def participant(row, user):
    return row.higher_user if row.lower_user_id == user.pk else row.lower_user


def message_data(row, user):
    return {'id': str(row.pk), 'sender_username': row.sender.username, 'body': row.body,
        'created_at': row.created_at.isoformat(), 'is_mine': row.sender_id == user.pk}


def conversation_data(row, user):
    other = participant(row, user)
    read_id = row.lower_read_id if row.lower_user_id == user.pk else row.higher_read_id
    last = row.messages.select_related('sender').first()
    accounts = connected_accounts(other)
    avatar = next((item['avatar_url'] for item in accounts if item.get('avatar_url')), '')
    return {'id': str(row.pk), 'participant': {'username': other.username,
        'full_name': other.full_name, 'avatar_url': avatar},
        'last_message': message_data(last, user) if last else None,
        'unread_count': row.messages.filter(pk__gt=read_id).exclude(sender=user).count(),
        'can_message': bool(enabled(user) and user.email_verified and enabled(other)),
        'updated_at': row.updated_at.isoformat()}


class ConversationInput(StrictSerializer):
    username = serializers.CharField(max_length=30)


class MessageInput(StrictSerializer):
    body = serializers.CharField(min_length=1, max_length=5000)


class ReadInput(StrictSerializer):
    through_message_id = serializers.CharField(max_length=19, allow_null=True)

    def validate_through_message_id(self, value):
        if value is None:
            return None
        if not value.isascii() or not value.isdecimal() or not 0 < int(value) <= 9223372036854775807:
            raise ValidationError('Geçerli bir mesaj kimliği girin.')
        return int(value)


class ConversationsView(ProtectedView):
    def get(self, request):
        throttle(request)
        rows, metadata = page_data(conversations_for(request.user), request)
        return Response({'conversations': [conversation_data(row, request.user) for row in rows], **metadata})

    def post(self, request):
        throttle(request, 'direct-start', 20)
        data = validated(ConversationInput, request)
        normalized = username_key(data['username'])
        target = get_object_or_404(User, username_normalized=normalized, is_active=True)
        if target.pk == request.user.pk:
            raise ValidationError({'username': ['Kendinize mesaj gönderemezsiniz.']})
        with transaction.atomic():
            users = {user.pk: user for user in User.objects.select_for_update().filter(
                pk__in={request.user.pk, target.pk}).order_by('pk')}
            actor = locked_user(request)
            require_sender(actor)
            target = users.get(target.pk)
            if (not target or target.username_normalized != normalized
                    or not enabled(target) or not profile_visible(target, actor)):
                raise NotFound()
            low, high = sorted([actor.pk, target.pk])
            row, created = Conversation.objects.get_or_create(lower_user_id=low, higher_user_id=high)
            result = conversation_data(row, actor)
        return Response({'conversation': result}, status=201 if created else 200)


def locked_conversation(request, conversation_id):
    initial = get_object_or_404(conversations_for(request.user), pk=conversation_id)
    users = {user.pk: user for user in User.objects.select_for_update().filter(
        pk__in={initial.lower_user_id, initial.higher_user_id}).order_by('pk')}
    actor = locked_user(request)
    row = get_object_or_404(conversations_for(actor).select_for_update(), pk=conversation_id)
    other = users.get(participant(row, actor).pk)
    if not other:
        raise NotFound()
    return row, actor, other


class MessagesView(ProtectedView):
    def get(self, request, conversation_id):
        throttle(request)
        row = get_object_or_404(conversations_for(request.user), pk=conversation_id)
        before = query_value(request, 'before', limit=19)
        if before and (not before.isascii() or not before.isdecimal() or not 0 < int(before) <= 9223372036854775807):
            raise ValidationError({'before': ['Geçerli bir mesaj kimliği girin.']})
        query = row.messages.select_related('sender')
        if before:
            query = query.filter(pk__lt=int(before))
        rows = list(query[:31])
        more = len(rows) > 30
        rows = rows[:30]
        return Response({'conversation': conversation_data(row, request.user),
            'messages': [message_data(item, request.user) for item in reversed(rows)],
            'next_before': str(rows[-1].pk) if more else None})

    def post(self, request, conversation_id):
        throttle(request, 'direct-send', 30)
        data = validated(MessageInput, request)
        with transaction.atomic():
            row, actor, other = locked_conversation(request, conversation_id)
            require_sender(actor)
            if not enabled(other):
                raise PermissionDenied({'detail': 'Bu hesaba şu anda mesaj gönderilemiyor.', 'code': 'recipient_unavailable'})
            message = Message.objects.create(conversation=row, sender=actor, body=data['body'])
            row.updated_at = timezone.now()
            row.save(update_fields=['updated_at'])
            result = {'message': message_data(message, actor), 'conversation': conversation_data(row, actor)}
        return Response(result, status=201)


class ReadView(ProtectedView):
    def post(self, request, conversation_id):
        throttle(request)
        displayed_id = validated(ReadInput, request)['through_message_id']
        with transaction.atomic():
            row, actor, other = locked_conversation(request, conversation_id)
            field = 'lower_read_id' if row.lower_user_id == actor.pk else 'higher_read_id'
            if displayed_id is not None:
                if not row.messages.filter(pk=displayed_id).exists():
                    raise ValidationError({'through_message_id': ['Bu konuşmadaki bir mesajı seçin.']})
                setattr(row, field, max(getattr(row, field), displayed_id))
                row.save(update_fields=[field])
            # A message arriving after GET remains unread until actually displayed.
            remaining = row.messages.filter(pk__gt=getattr(row, field)).exclude(sender=actor).count()
        return Response({'unread_count': remaining})
