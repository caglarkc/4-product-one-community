import unicodedata
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


def username_key(value):
    return unicodedata.normalize('NFC', value).casefold()


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **fields):
        user = self.model(email=email.strip().lower(), **fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **fields):
        return self.create_user(email, password, is_staff=True, is_superuser=True, **fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30)
    username_normalized = models.CharField(max_length=90, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    birth_date = models.DateField(null=True)
    gender = models.CharField(max_length=11, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    security_version = models.PositiveIntegerField(default=1)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    objects = UserManager()

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='account_email_case_insensitive')]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        self.username = unicodedata.normalize('NFC', self.username)
        self.username_normalized = username_key(self.username)
        if kwargs.get('update_fields'):
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'email', 'username', 'username_normalized'}
        super().save(*args, **kwargs)


class SessionRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    security_version = models.PositiveIntegerField()
