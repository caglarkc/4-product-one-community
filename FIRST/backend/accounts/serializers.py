import re
import unicodedata
from datetime import date
from django.conf import settings
from django.contrib.auth.password_validation import CommonPasswordValidator
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import User, username_key
from .security import digest

# Repository-authored baseline of obvious password variants; not a breach corpus.
# Django CommonPasswordValidator supplies its shipped common-password corpus;
# a deployment can additionally supply a provenance-reviewed offline breach list.
BREACHED_HASHES = {digest(p) for p in ('Password1!', 'Password123!', 'Qwerty123!', 'Welcome1!', 'P@ssw0rd', 'P@ssw0rd!')}


def password_policy(value):
    if not 8 <= len(value) <= 20 or any(c.isspace() for c in value):
        raise serializers.ValidationError('Şifre boşluksuz 8–20 karakter olmalıdır.')
    if not (any(c.isupper() for c in value) and any(c.islower() for c in value)
            and any(c.isdigit() for c in value) and any(not c.isalnum() for c in value)):
        raise serializers.ValidationError('Büyük harf, küçük harf, sayı ve özel karakter gereklidir.')
    try:
        CommonPasswordValidator().validate(value)
    except ValidationError:
        raise serializers.ValidationError('Bu şifre yaygın veya güvenli değil.')
    if digest(value) in BREACHED_HASHES | settings.AUTH_BREACHED_PASSWORD_HASHES:
        raise serializers.ValidationError('Bu şifre yaygın veya güvenli değil.')
    return value


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['JSON nesnesi gereklidir.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({field: ['Bilinmeyen alan.'] for field in sorted(unknown)})
        return super().to_internal_value(data)


class NormalizedUsernameField(serializers.CharField):
    def to_internal_value(self, data):
        # Normalize before CharField performs blank and length validation.
        if isinstance(data, str):
            data = unicodedata.normalize('NFC', data)
        return super().to_internal_value(data)


class ProfileSerializer(StrictSerializer):
    username = NormalizedUsernameField(min_length=3, max_length=30)
    full_name = serializers.CharField(max_length=150)
    birth_date = serializers.DateField()
    gender = serializers.ChoiceField(choices=['female', 'male', 'other', 'unspecified'])
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_username(self, value):
        value = unicodedata.normalize('NFC', value)
        if not all(c.isalnum() or c == '_' for c in value):
            raise serializers.ValidationError('Yalnız harf, rakam ve alt çizgi kullanın.')
        query = User.objects.filter(username_normalized=username_key(value))
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError('Bu kullanıcı adı kullanılıyor.')
        return value

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError('En az 13 yaşında olmalısınız.')
        return value

    def validate_phone(self, value):
        if not value:
            return ''
        value = re.sub(r'[\s()\-]', '', value)
        if not re.fullmatch(r'\+[1-9][0-9]{7,14}', value):
            raise serializers.ValidationError('Uluslararası telefon biçimini kullanın (+ ve 8–15 rakam).')
        return value


class RegisterSerializer(ProfileSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, validators=[password_policy], write_only=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Bu e-posta kullanılıyor.')
        return value


class LoginSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, max_length=256, write_only=True)
    remember_me = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if 'remember_me' in self.initial_data and type(self.initial_data['remember_me']) is not bool:
            raise serializers.ValidationError({'remember_me': ['Boolean gereklidir.']})
        attrs['email'] = attrs['email'].strip().lower()
        return attrs


def user_data(user):
    complete = bool(user.full_name and user.username and user.birth_date and user.gender)
    return {'id': user.pk, 'email': user.email, 'username': user.username,
            'full_name': user.full_name, 'birth_date': user.birth_date.isoformat() if user.birth_date else None,
            'gender': user.gender, 'phone': user.phone, 'email_verified': user.email_verified,
            'phone_verified': user.phone_verified, 'profile_complete': complete,
            'providers': list(user.socialaccount_set.values_list('provider', flat=True).distinct()),
            'has_usable_password': user.has_usable_password(), 'capabilities': {'can_apply': False, 'can_create_listing': False}}
