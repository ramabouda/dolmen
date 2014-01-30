#!/usr/bin/python
#vim: set fileencoding=utf-8 :

from django.db import models
from tribe import Tribe
from report import Report


class Grade(models.Model):
    name = models.CharField(max_length=30)
    alliance = models.ForeignKey('Alliance')

    class Meta:
        app_label = 'game'

    def __unicode__(self):
        return self.name


class Alliance(models.Model):
    name = models.CharField(max_length=50)
    abreviation = models.CharField(max_length=5)
    
    class Meta:
        app_label = 'game'
    
    def __unicode__(self):
        return self.name

    def members_number(self):
        return self.tribe_set.all().count()

    def addMember(self, tribe):
        """ add a member and notify it """
        tribe.alliance = self
        tribe.save()
        filter(
                lambda t: Report.obejcts.create(
                    tribe=t,
                    type=5,
                    param1=t.name
                    ),
                Tribe.objects.filter(alliance=self)
                )

    def excludeMember(self, tribe):
        """ exclude en member and notify it	"""
        tribe.alliance = None
        tribe.save()
        filter(
                lambda t: Report.objects.create(
                    tribe=t,
                    type=6,
                    param1=t.name
                    ),
                Tribe.objects.filter(alliance=self)
                )

    def changeGrade(self, tribe, grade):
        """ change the grade and notufy it """
        tribe.grade = grade
        tribe.save()
        filter(
            lambda t: Report.objects.create(
                tribe=t,
                type=7,
                param1=grade.name),
            Tribe.objects.filter(alliance=self)
            )
