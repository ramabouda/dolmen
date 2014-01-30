#!/usr/bin/python
#vim: set fileencoding=utf-8 :
from django.conf import settings
from django.db import models


class Building(models.Model):
    name = models.CharField(max_length=50, unique=True)
    identifier = models.CharField(max_length=20, unique=True) #identifier for coding, in english
    cost = models.OneToOneField('Cost', null=True, blank=True)
    creation_time = models.PositiveSmallIntegerField(default=10)

    class Meta:
        app_label = 'game'

    def image_url(self):
        return '%sgame/images/buildings/%s.png' % (settings.STATIC_URL, self.identifier)
    
    def get_construction_duration(self, level, tribe):
        total = self.cost.resources.wood + \
                self.cost.resources.skin + \
                self.cost.resources.food + \
                self.cost.resources.silex
        
        tech_coeff = 1+tribe.get_techno_level_by_name('wood_work')/10
        return total*4*level/tech_coeff
    


class ConstructedBuilding(models.Model):
    building = models.ForeignKey(Building)
    village = models.ForeignKey('Village')
    level = models.PositiveSmallIntegerField(default=1)
    
    class Meta:
        app_label = 'game'
        
    def can_construct_next(self):
        return self.village.can_pay(self.cost_next_upgrade())
    
    def cost_upgrade(self, level):
        if level==1:
            return self.building.cost
        temp = (self.building.cost * (level-1)*0.3 + self.cost_upgrade(level-1))
        temp.round()
        return temp

    def cost_next_upgrade(self):
        return self.cost_upgrade(self.level)
    
