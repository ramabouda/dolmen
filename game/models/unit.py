#vim: set fileencoding=utf-8 :

from collections import Counter
from django.conf import settings
from django.db import models
from technology import Technology
from game.utils.constants import RANGED_UNITS


class UnitType(models.Model):
    """
    Ancestor class for both :model:`game.Human` and :model:`game.Animal`.
    Provides common fields like fight behavior, and management
    methods
    """
    name = models.CharField(max_length=50, unique=True)
    identifier = models.CharField(max_length=20, unique=True) #identifier for coding, in english
    attack = models.PositiveSmallIntegerField(default=100)
    defense = models.PositiveSmallIntegerField(default=100)
    speed = models.PositiveSmallIntegerField(default=10)
    description = models.TextField(max_length=5000, null=True, blank=True)

    class Meta:
        app_label = 'game'

    def __unicode__(self):
        return self.name

    def calcule_pv(self, tribe=None):
        #TODO
        return self.defense * 3

    def compute_attack(self, tribe=None, opponent_tribe=None):
        #TODO avec plein de ifs partout
        return self.attack
    
    def compute_defense(self, tribe=None, opponent_tribe=None):
        #TODO avec plein de ifs partout
        return self.defense
    
    def is_ranged(self):
        """ True if the unit has the "ranged" skill """
        try :
            RANGED_UNITS.index(self.name)
            return True
        except Exception:
            False

    def image_url(self):
        return "%sgame/images/units/%s.png" % (settings.STATIC_URL, self.identifier)

    def small_image_url(self):
        return "{}game/images/units/small/{}.png"\
                .format(settings.STATIC_URL, self.identifier)
            

class Human(UnitType):
    """
    designs a human kind of unit. Inherits from
    :model:`game:UnitType` for fighting behaviour,
    but has a economical concerns as well as technological
    ones.
    """
    #per hour
    consumption = models.PositiveSmallIntegerField(default=10)
    cost = models.OneToOneField('Cost')
    #in seconds
    creation_time = models.PositiveSmallIntegerField(default=100)

    class Meta:
        app_label = 'game'
        
    def compute_attack(self, tribe=None, opponent_tribe=None):
        """get the attack of the :model:`game.Human`, considering the
        :model:`game.TechnologyKnowledge` of the owner’s and oponent’s 
        :model:`game.Tribe` """
        #TODO avec plein de ifs partout
        attack = UnitType.compute_attack(self, tribe, opponent_tribe)
        
        attack += self.attack*0.03*tribe.get_techno_level_by_name('carved_stone')
        if self.is_ranged():
            attack += self.attack*0.05*tribe.get_techno_level_by_name('bone_work')
        else:
            attack += self.attack*0.03*tribe.get_techno_level_by_name('bone_work')
            attack += self.attack*0.05*tribe.get_techno_level_by_name('spear')
        if self.identifier == 'hunter':
            attack += self.attack*0.10*tribe.get_techno_level_by_name('assagai')
        elif self.identifier == 'prowler':
            attack += self.attack*0.10*tribe.get_techno_level_by_name('archery')
        elif self.identifier == 'brute':
            attack += self.attack*0.05*tribe.get_techno_level_by_name('spear')
        elif self.identifier == 'tribal_warrior':
            attack += self.attack*0.02*tribe.get_techno_level_by_name('pictorial_art')
        return attack
    
    def compute_defense(self, tribe=None, opponent_tribe=None):        
        """get the defense of the :model:`game.Human`, considering the
        :model:`game.TechnologyKnowledge` of the owner’s and oponent’s 
        :model:`game.Tribe` """
        defense = UnitType.compute_defense(self, tribe, opponent_tribe)
        defense += self.attack*0.03*tribe.get_techno_level_by_name('tanning')
        defense += self.attack*0.05*tribe.get_techno_level_by_name('sewing')
        if not self.is_ranged():
            defense += self.defense*0.05*tribe.get_techno_level_by_name('boiled_leather')
        if self.identifier == 'tough_guy':
            defense += self.defense*0.05*tribe.get_techno_level_by_name('boiled_leather')
        elif self.identifier == 'tribal_warrior':
            defense += self.defense*0.02*tribe.get_techno_level_by_name('pictorial_art')
        return defense

    def missing_requirements(self, tribe):
        "get a Counter object with the difference between requirements and knowledges"
        requirements = self.unitrequirement.all().values_list('need', 'level_required')
        knowledges = tribe.technologyknowledge_set.values_list('technology', 'level')
        creq = Counter({a:b for (a, b) in requirements})
        cknow = Counter({a:b for (a, b) in knowledges})
        diff = creq - cknow
        return (diff)


class UnitRequirement(models.Model):
    need = models.ForeignKey(Technology)
    target = models.ForeignKey(Human)
    level_required = models.PositiveSmallIntegerField()

    class Meta:
        app_label = 'game'
        unique_together = ('need', 'target')


class Animal(UnitType):
    drops = models.ForeignKey('Resources')

    class Meta:
        app_label = 'game'
        verbose_name_plural = 'Animaux'
