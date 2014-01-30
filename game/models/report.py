#!/usr/bin/python
#vim: set fileencoding=utf-8 :

from django.db import models
from django.template.loader import render_to_string

REPORT_TYPES = (
        (1, 'combat'),
        (2, 'ennemy approaching'),
        (5, 'starvation begin'),
        (10, 'mission achieved'),
        (11, 'mission failed'),
        (20, 'group came back'),
        (21, 'resources received'),
        (30, 'alliance message'),
        )
#(1, 'building finished'),
    #(2, 'unit produced'),
    #(3, 'fight'),
    #(4, 'ennemy approaching'),
    #(5, 'alliance new member'),
    #(6, 'alliance exclude member'),
    #(7, 'alliance change grade'),
    #(20, 'mission complete : found'),
    #(21, 'mission complete : carry'),
    #(22, 'mission complete : received resources from another tribe'),

class Report(models.Model):
    type = models.PositiveSmallIntegerField(choices=REPORT_TYPES)
    tribe = models.ForeignKey('Tribe')
    village = models.ForeignKey('Village', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    subject = models.CharField(max_length=127)
    body = models.TextField(max_length=2047)

    def html(self):
        return render_to_string('game/report.html', {'report':self})
    
    class Meta:
        app_label = 'game'
        ordering = ['-date']
