# -*- coding: utf-8 -*-
from muckrock import MuckRock
from muckrockbot.models import Request
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Save requests from the MuckRock API"

    def handle(self, *args, **options):
        client = MuckRock()
        [self.save(req) for req in client.foia.get(ordering="-datetime_submitted", has_datetime_submitted=True)]
        [self.save(req) for req in client.foia.get(ordering="-datetime_done", status="done")]

    def save(self, req):
        obj, created = Request.objects.get_or_create(muckrock_id=req['id'])
        if not created:
            return
        print("Created {}".format(req['title']))
        obj.title = req['title']
        obj.slug = req['slug']
        obj.status = req['status']
        obj.username = req['username']
        obj.datetime_submitted = req['datetime_submitted']
        obj.datetime_done = req['datetime_done']
        obj.absolute_url = req['absolute_url']
        obj.save()
