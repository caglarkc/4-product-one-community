from getpass import getpass
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from core.models import Category,Policy,User
class Command(BaseCommand):
    help='Create a real operator account and agreed categories; no fake jobs or university domains.'
    def add_arguments(self,parser):parser.add_argument('--email',required=True);parser.add_argument('--name',required=True)
    @transaction.atomic
    def handle(self,*args,**options):
        if User.objects.filter(email=options['email'].casefold()).exists():raise CommandError('Account exists; use Django admin to manage permissions.')
        password=getpass('Operator password: ');validate_password(password)
        User.objects.create_superuser(options['email'],password,display_name=options['name'],roles=[])
        for name in ['Yazılım','Veri / AI','Tasarım','Video','Çeviri','İçerik']:Category.objects.get_or_create(name=name)
        Policy.objects.get_or_create(pk=1)
        self.stdout.write('Operator and categories created. Product prices and university domains remain unset.')
