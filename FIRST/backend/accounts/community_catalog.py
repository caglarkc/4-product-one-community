"""Shared, server-owned skills/technology vocabulary and search helpers."""
import unicodedata
from django.db.models import F, Q, Value
from django.db.models.functions import Lower, Replace
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

SKILLS = [{'value': key, 'label': label} for key, label in [
    ('python', 'Python'), ('javascript', 'JavaScript'), ('typescript', 'TypeScript'),
    ('react', 'React'), ('nextjs', 'Next.js'), ('vue', 'Vue'), ('angular', 'Angular'),
    ('django', 'Django'), ('fastapi', 'FastAPI'), ('nodejs', 'Node.js'), ('go', 'Go'),
    ('java', 'Java'), ('kotlin', 'Kotlin'), ('swift', 'Swift'), ('csharp', 'C#'),
    ('cpp', 'C++'), ('rust', 'Rust'), ('php', 'PHP'), ('ruby', 'Ruby'),
    ('dart', 'Dart'), ('flutter', 'Flutter'), ('react-native', 'React Native'),
    ('html-css', 'HTML / CSS'), ('sql', 'SQL'), ('postgresql', 'PostgreSQL'),
    ('mysql', 'MySQL'), ('mongodb', 'MongoDB'), ('redis', 'Redis'),
    ('docker', 'Docker'), ('kubernetes', 'Kubernetes'), ('linux', 'Linux'),
    ('git', 'Git'), ('ci-cd', 'CI/CD'), ('aws', 'AWS'), ('azure', 'Azure'),
    ('gcp', 'Google Cloud'), ('machine-learning', 'Makine öğrenmesi'),
    ('data-analysis', 'Veri analizi'), ('security', 'Güvenlik'), ('testing', 'Test'),
    ('ui-design', 'Arayüz tasarımı'), ('ux-research', 'Kullanıcı araştırması'),
    ('accessibility', 'Erişilebilirlik'), ('documentation', 'Dokümantasyon'),
    ('translation', 'Çeviri'), ('project-management', 'Proje yönetimi')]]
SKILL_IDS = [item['value'] for item in SKILLS]
REASONS = [{'value': key, 'label': label} for key, label in [
    ('spam', 'Spam'), ('harassment', 'Taciz'), ('inappropriate', 'Uygunsuz içerik'),
    ('misleading', 'Yanıltıcı bilgi'), ('other', 'Diğer')]]


class CatalogList(serializers.ListField):
    def __init__(self, choices=SKILL_IDS, limit=12, **kwargs):
        super().__init__(child=serializers.ChoiceField(choices=choices), max_length=limit, **kwargs)

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        if len(set(result)) != len(result):
            raise serializers.ValidationError('Aynı seçenek birden fazla eklenemez.')
        return result


def query_value(request, name, choices=None, limit=100):
    values = request.query_params.getlist(name)
    if len(values) > 1 or (values and len(values[0]) > limit):
        raise ValidationError({name: ['Geçerli bir filtre girin.']})
    value = values[0].strip() if values else ''
    if choices is not None and value and value not in choices:
        raise ValidationError({name: ['Geçerli bir filtre seçin.']})
    return value


def search(queryset, request, fields):
    value = query_value(request, 'q')
    if not value:
        return queryset
    value = unicodedata.normalize('NFC', value).replace('İ', 'i').replace('I', 'i').replace('ı', 'i').lower()
    condition = Q()
    for index, field in enumerate(fields):
        alias = f'_community_search_{index}'
        # Normalize I before lower() so database locale cannot change its meaning.
        expression = Lower(Replace(Replace(F(field), Value('İ'), Value('i')), Value('I'), Value('i')))
        expression = Replace(expression, Value('ı'), Value('i'))
        queryset = queryset.annotate(**{alias: expression})
        condition |= Q(**{alias + '__contains': value})
    return queryset.filter(condition)


def page_data(queryset, request):
    value = query_value(request, 'page', limit=9) or '1'
    if not value.isascii() or not value.isdecimal() or int(value) < 1:
        raise ValidationError({'page': ['Sayfa pozitif bir tam sayı olmalıdır.']})
    page, size = int(value), 12
    count = queryset.count()
    start = (page - 1) * size
    return (queryset[start:start + size] if start < count else []), {
        'count': count, 'next_page': page + 1 if start + size < count else None,
        'previous_page': page - 1 if page > 1 else None}
