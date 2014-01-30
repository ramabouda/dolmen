#!vim: set fileencoding=utf-8 :

from django.db import models
from resources import Cost
from django.conf import settings


class Technology(models.Model):
    name = models.CharField(max_length=25)
    identifier = models.CharField(max_length=20, unique=True) #identifier for coding, in english
    image = models.FileField(upload_to=".", blank=True, null=True)
    cost = models.OneToOneField(Cost)

    class Meta:
        app_label = 'game'

    def __unicode__(self):
        return self.name

    def research_cost(self, level):
        if level == 1:
            return self.cost
        # TODO
      #return self.research_cost(level-1) + level * self.cost * 0.3
        return self.cost

    #def missing_requirements(self, tribe):
    #Quietly depreciated!
        #requirements = self.need.values_list('need', 'level_required')
        #knowledges = tribe.technologyknowledge_set.values_list('technology', 'level')
        #creq = Counter(requirements)
        #cknow = Counter(knowledges)
        #return dict(creq - cknow)

    def get_research_duration(self, level):
        """Return the time (in s) needed to discover the technology for the needed level"""
        #TODO
        return 3*level

    def image_url(self):
        return '{}game/images/techno/{}.png'.format(settings.STATIC_URL, self.identifier)


class Requirement(models.Model):
    need = models.ForeignKey(Technology, related_name="target")
    target = models.ForeignKey(Technology, related_name="need")
    level_required = models.PositiveSmallIntegerField()

    class Meta:
        app_label = 'game'


class TechnologyKnowledge(models.Model):
    technology = models.ForeignKey(Technology)
    level = models.PositiveSmallIntegerField(default=1)
    tribe = models.ForeignKey('Tribe', blank=True, null=True, default=None)

    class Meta:
        app_label = 'game'
        unique_together = ('tribe', 'technology')
        
    def cost_upgrade(self, level):
        if level==1:
            return self.technology.cost
        temp = (self.technology.cost * (level-1)*0.3 + self.cost_upgrade(level-1))
        temp.round()
        return temp

    def cost_next_upgrade(self):
        return self.cost_upgrade(self.level)
