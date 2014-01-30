#!/usr/bin/python
#vim: set fileencoding=utf-8 :

from django.core.urlresolvers import reverse
from django.db import models
from tribe import Tribe


class Thread(models.Model):
    author = models.ForeignKey(Tribe, related_name='initiated_threads')
    recipients = models.ManyToManyField(
            Tribe,
            related_name='received_thread',
            )
    subject = models.CharField(max_length=64)

    class Meta:
        app_label = 'game'

    def get_absolute_url(self):
        #TODO
        pass


class Message(models.Model):
    author = models.ForeignKey(Tribe, related_name='sent_messages')
    date_add = models.DateTimeField(auto_now_add=True)
    date_edit = models.DateTimeField(blank=True)
    content = models.TextField(max_length=65535)
    thread = models.ForeignKey(Thread)
    readers = models.ManyToManyField(Tribe, related_name='read_messages', null=True, blank=True)

    class Meta:
        app_label = 'game'
        get_latest_by = 'date_add'
        ordering = ['date_add']
