import time
from muckrockbot.models import Request
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Make tweets at @muckrockbot"

    def handle(self, *args, **options):
        request_list = Request.objects.untweeted()[:2]
        for req in request_list:
            print("Tweeting {}".format(req))
            req.post()
            time.sleep(3)
