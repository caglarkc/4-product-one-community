import time
from django.core.management.base import BaseCommand
from core.operations import tick
class Command(BaseCommand):
    help='Durable STEP outbox and due predicates. No remote ambiguous mutation is blindly retried.'
    def add_arguments(self,parser):
        parser.add_argument('--loop',action='store_true')
        parser.add_argument('--interval',type=int,default=30)
    def handle(self,*args,**options):
        while True:
            tick()
            if not options['loop']:break
            time.sleep(max(1,options['interval']))
