import time
from muckrockbot.models import Request
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Make tweets at @muckrockbot"

    def handle(self, *args, **options):
        request_list = Request.submitted.untweeted().order_by("-datetime_submitted")[:10]
        for req in request_list:
            print("Tweeting {}".format(req))
            req.post_submission()
            time.sleep(3)

        request_list = Request.completed.untweeted().order_by("-datetime_done")[:10]
        for req in request_list:
            print("Tweeting {}".format(req))
            req.post_completion()
            time.sleep(3)
