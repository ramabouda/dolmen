#!/usr/bin/python
#vim: set fileencoding=utf-8 :

from collections import Counter
from decimal import Decimal
from django.db import models
from django.template.loader import render_to_string


RESOURCE_CHOICES = (
        ('wood', 'Bois'),
        ('food', 'Nourriture'),
        ('silex', 'Silex'),
        ('skin', 'Peaux'),
        )


class Resources(models.Model):
    wood = models.DecimalField(
            default=0,
            max_digits=11,
            decimal_places=2,
            )
    food = models.DecimalField(
            default=0,
            max_digits=11,
            decimal_places=2,
            )
    silex = models.DecimalField(
            default=0,
            max_digits=11,
            decimal_places=2,
            )
    skin = models.DecimalField(
            default=0,
            max_digits=11,
            decimal_places=2,
            )
    
    
    def set_to_zero(self):
        self.food = 0
        self.wood = 0
        self.skin = 0
        self.silex = 0
        self.save()

    class Meta:
        app_label = 'game'
        verbose_name_plural = 'Resources'

    def __unicode__(self):
        return unicode(self.id)

# TODO gestion des types
    def __iadd__(self, other):
        self.wood += Decimal(other.wood)
        self.food += Decimal(other.food)
        self.silex += Decimal(other.silex)
        self.skin += Decimal(other.skin)
        return self

    def __ge__(self, other):
        return self.__class__ == other.__class__\
                and self.wood >= other.wood\
                and self.food >= other.food\
                and self.silex >= other.silex\
                and self.skin >= other.skin

    def __eq__(self, other):
        return self.__class__ == other.__class__\
                and self.wood == other.wood\
                and self.food == other.food\
                and self.silex == other.silex\
                and self.skin == other.skin

#    def __ne__(self, other):
#        return self.__class__ <> other.__class__\
#                or self.wood != other.wood\
#                or self.food != other.food\
#                or self.silex != other.silex\
#                or self.skin != other.skin

    def __lt__(self, other):
        return self.__class__ == other.__class__\
                and self.wood < other.wood\
                and self.food < other.food\
                and self.silex < other.silex\
                and self.skin < other.skin

    def __gt__(self, other):
        return self.wood > other.wood\
                and self.food > other.food\
                and self.silex > other.silex\
                and self.skin > other.skin

    def __le__(self, other):
        return self.wood <= other.wood\
                and self.food <= other.food\
                and self.silex <= other.silex\
                and self.skin <= other.skin

    def __add__(self, other):
        return Resources(
                wood=Decimal(self.wood) + Decimal(other.wood),
                food=Decimal(self.food) + Decimal(other.food),
                silex=Decimal(self.silex) + Decimal(other.silex),
                skin=Decimal(self.skin) + Decimal(other.skin),
                )

    def __isub__(self, other):
        self.wood -= Decimal(other.wood)
        self.food -= Decimal(other.food)
        self.silex -= Decimal(other.silex)
        self.skin -= Decimal(other.skin)
        return self

    def __radd__(self, other):
        return Resources(
                wood=self.wood + other.wood,
                food=self.food + other.food,
                silex=self.silex + other.silex,
                skin=self.skin + other.skin,
                )

    def __sub__(self, other):
        return Resources(
                wood=self.wood - Decimal(other.wood),
                food=self.food - Decimal(other.food),
                silex=self.silex - Decimal(other.silex),
                skin=self.skin - Decimal(other.skin),
                )

    def __rsub__(self, other):
        return Resources(
                wood=Decimal(other.wood) - self.wood,
                food=Decimal(other.food) - self.food, 
                silex=Decimal(other.silex) - self.silex,
                skin=Decimal(other.skin) - self.skin,
                )

    def __rmul__(self, other):
        return Resources(
                wood=self.wood.__float__() * other,
                food=self.food.__float__() * other,
                silex=self.silex.__float__() * other,
                skin=self.skin.__float__() * other,
                )

    def __mul__(self, other):
        return Resources(
                wood=self.wood.__float__() * other,
                food=self.food.__float__() * other,
                silex=self.silex.__float__() * other,
                skin=self.skin.__float__() * other,
                )

    def __iter__(self):
        liste = ['wood', 'food', 'skin', 'silex']
        return liste.__iter__()

    def __getitem__(self, key):
        if key in ['wood', 'food', 'skin', 'silex']:
            return getattr(self, key)
        else:
            raise KeyError

    def __setitem__(self, key, value):
        if key in ['wood', 'food', 'skin', 'silex']:
            setattr(self, key, value)
        else:
            raise KeyError

    @classmethod
    def dict_to_resources(dicto):
        "make a resources object from a dict. Does not save the new resources"
        dicto = Counter(dicto)
        if not (dicto['wood'] or dicto['food']
                or dicto['skin'] or dicto['silex']):
            return None
        return Resources(
                wood=dicto['wood'],
                food=dicto['food'],
                skin=dicto['skin'],
                silex=dicto['silex'],
                )
    
    def to_dict(self):
        return {
                'wood': self.wood,
                'food': self.food,
                'skin': self.skin,
                'silex': self.silex,
                }
    
    def round(self):
        for (k,v) in self.to_dict().items():
            setattr(self, k, round(v))


class Cost(models.Model):
    resources = models.OneToOneField(Resources, default=Resources())
    divinity = models.PositiveSmallIntegerField(default=0)
    fertility = models.PositiveSmallIntegerField(default=0)

    resources_ordonned = ['food', 'wood', 'skin', 'silex', 'fertility', 'divinity']

    class Meta:
        app_label = 'game'

    def __mul__(self, other):
        return Cost(
                resources=other * self.resources,
                divinity=other * self.divinity,
                fertility=other * self.fertility,
                )

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        self = self * other

    def __add__(self, other):
        return Cost(
                resources=other.resources + self.resources,
                divinity=other.divinity + self.divinity,
                fertility=other.fertility + self.fertility,
                )

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        self = self + other

    def can_pay(self, cost):
        "True if it's greater than cost"
        return self.divinity >= cost.divinity\
                and self.fertility >= cost.fertility\
                and self.resources >= cost.resources

    def html(self):
        cost = self.resources.to_dict().items() + [('divinity', self.divinity), ('fertility',self.fertility)]
        final_cost = [(k,v) for k,v in cost if v!=0 ]
        return render_to_string(
                'game/cost.html',
                {
                    'cost': final_cost,
                    
                },
                )
    
    def round(self):
        self.divinity = round(self.divinity)
        self.fertility = round(self.fertility)
        self.resources.round()

    def delete(self):
        self.resources.delete()
        return super(Cost, self).delete()


class Gathering(models.Model):
    date_update = models.DateTimeField(auto_now=True)
    group = models.OneToOneField('Group')
    village = models.ForeignKey('Village')
    resource = models.CharField(max_length=10, choices=RESOURCE_CHOICES, default='food')
    efficiency = models.FloatField(default=1) #from 0 to 1
    production = models.FloatField(default=50) #gathering per hour

    class Meta:
        app_label = 'game'

    @staticmethod
    def add_gathering(group):
        d = group.position.distance(group.village.position)
        if d:
            efficiency = max(0.1, 0.9-(d-1)*0.2)
        else:
            efficiency = 1
        resource = group.position.get_resource()
        a = Gathering.objects.create(
                group=group,
                village=group.village,
                resource=resource,
                efficiency=efficiency,
                )
        group.position.compute_gathering_production()
        group.village.update_income()
        return a

    def delete(self):
        village = self.village
        super(Gathering, self).delete()
        village.update_income()
