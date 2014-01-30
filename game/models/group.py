#vim: set fileencoding=utf-8 :

from annoying.functions import get_object_or_None
from collections import Counter
from django.db import models, transaction
from django.db.models import Min
from django.template.loader import render_to_string
from game.utils.constants import MEAN_DELAYS
from random import choice
from resources import Resources, Gathering
from unit import UnitType
import logging

logger = logging.getLogger(__name__)


class PayError(Exception):
    logger.debug("PayError thrown")
    pass


class UnitStack(models.Model):
    """
    Représentation des unités d’un group sous forme
    de piles d’unités d’un type donné. Chaque group
    a au plus une pile d’unités de chaque type, et
    au moins une pile d’unités.
    """
    unit_type = models.ForeignKey('UnitType')
    group = models.ForeignKey('Group')
    number = models.PositiveSmallIntegerField()

    class Meta:
        app_label = 'game'
        verbose_name_plural = "Piles d'unités"
        verbose_name = "Pile d'unités"
        unique_together = ('unit_type', 'group')

    def __unicode__(self):
        return '%s %ss' % (self.number, self.unit_type.name)

    def kill_guys(self, number):
        if number >= self.number:
            logger.debug("destroying group {} while killing {} units".format(self.id, number))
            self.delete()
        else:
            self.number -= number
            logger.debug("killing {} in group {}".format(number, self.id))
            self.save()


class GroupManagementMixin:
    """Provide some handy methods to manage both human
    and animal groups"""
    def add_unit(self, list):
        """
        **param**
            une liste de tuples représentant les unités
            à ajouter au group, sous la forme
            [(unit, number)...]
        """
        for (identifier, number) in list:
            stack = get_object_or_None(
                    UnitStack,
                    group=self,
                    unit_type=UnitType.objects.get(identifier=identifier)
                    )
            if stack:
                stack.number += number
                stack.save()
            else:
                stack = UnitStack(
                        group=self,
                        unit_type=UnitType.objects.get(identifier=identifier),
                        number=number
                        )
                stack.save()

    def units_number(self):
        """ Sum of all the units """
        temp = 0
        for pile in self.unitstack_set.all():
            temp += pile.number
        return temp

    def merge(self, group):
        """
        Fusionne le group courant avec le
        group passé en argument. Le village
        de référence
        reste celui du group courant -> le group
        a.merge(b) dépendra du village de a
        """
        compo_group_inclu = group.unitstack_set.all()
        for stack in compo_group_inclu:
            stack_self = get_object_or_None(
                    UnitStack,
                    group=self,
                    unit_type=stack.unit_type
                    )
            if stack_self:
                stack_self.number += stack.number
                stack_self.save()
            else:
                stack.group_id = self.id
                stack.save()
        self.village.update_income()
        group.delete()
        logger.debug("successfully merged two groups")

    def to_list(self, opponent=None):
        """
        Déploie les données contenues dans les
        objets de type Group dans des listes
        de dictionnaires sous la forme
        [{'type', 'attack', 'pv'}]
        """
        liste = list()
        data = self.unitstack_set.all()
        for pile in data:
            try:
                pv = pile.unit_type.calcule_pv(self.get_tribe())
            # le cas où get_tribe ne marche pas
            except Exception:
                pv = pile.unit_type.calcule_pv()
            try:
                tribe_adverse = opponent.get_tribe()
                attack = pile.unit_type.calcule_attack(
                        self.get_tribe(),
                        tribe_adverse
                        )
            except Exception:
                try:
                    attack = pile.unit_type.calcule_attack(self.get_tribe())
                except Exception:
                    attack = pile.unit_type.calcule_attack()
            ajout = [
                    {
                        'type': pile.unit_type,
                        'attack': attack,
                        'pv': pv,
                        'pv_max': pv
                    }
                    ]*pile.number
            liste.extend(ajout)
        return liste

    def stacks_to_list(self):
        liste = []
        for stack in self.unitstack_set.all():
            liste.append((stack.unit_type.identifier, stack.number))
        return liste

    def can_move(self, new_position):
        return self.position.distance(new_position) <= 1

    def move(self, new_position):
        """
        Correspond à l’action de passer la frontière entre la tile courrante
        et la tile new_position. Si ce n’est pas possible, lève l’exception
        CannotMove
        """
        if not self.can_move(new_position):
            raise self.CannotMove(
            'Mouvement impossible en une étape jusqu’à la tile demandée : %s'
            % new_position
            )
        self.position = new_position
        self.save()

    def get_time_multiplier(self, tile=None):
        group_speed = self.unitstack_set.aggregate(
                Min('unit_type__speed')
                )['unit_type__speed__min']
        multiplier = group_speed/10
        if tile and tile.ground == 3:
            multiplier *= 2
        return multiplier

    def get_internal_move_delay(self, tile=None):
        multiplier = self.get_time_multiplier(None)
        return MEAN_DELAYS['internal_move']*multiplier

    def get_enter_delay(self, tile=None):
        multiplier = self.get_time_multiplier(None)
        return MEAN_DELAYS['enter']*multiplier

    def get_cross_delay(self, tile=None):
        multiplier = self.get_time_multiplier(None)
        return MEAN_DELAYS['cross']*multiplier

    class CannotMove(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)


class Group(models.Model, GroupManagementMixin):
    resources = models.OneToOneField(
        'Resources',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        )
    position = models.ForeignKey('Tile')
    village = models.ForeignKey('Village', null=True)

    class Meta:
        app_label = 'game'

    class CannotSplit(Exception):
        pass
        
    def steal(self, group):
        "get the most of the other group's resources it can"
        #TODO handle the max resources capacity
        if group.resources_id is None:
            return
        if self.resources is None:
            self.resources = group.resources
            group.resources = None
            group.save()
            self.save()
        else:
            self.resources += group.resources
            group.resources.delete()

    #TODO tests
    def take_resources(self, village_or_group, resources_dict):
        """
        Substract the max resources up to resources_dict content to the
        village_or_group’s resources and set it in a new resources object
        which is returned
        """
        for key in resources_dict:
            resources_dict[key] = max(resources_dict[key], 0)
        available_resources = village_or_group.resources
        wanted_resources = Resources.dict_to_resources(resources_dict)
        if available_resources >= wanted_resources:
            available_resources -= wanted_resources
            available_resources.save()
            wanted_resources.save()
            return wanted_resources
        else:
            received_resources = Resources()
            for key in wanted_resources:
                amount = min(wanted_resources[key], available_resources[key])
                received_resources[key] = amount
                available_resources -= amount
            available_resources.save()
            received_resources.save()
            return received_resources()

    def get_tribe(self):
        """
        return the tribe whose the group depends on
        """
        return self.village.tribe

    def __unicode__(self):
        if self.village:
            return 'group du village {}, tribe {}, {} unit'.format(
                            self.village.name,
                            self.get_tribe().name,
                            self.units_number(),
                            )
        else:
            return 'anonym group'

    def can_create_village(self):
        """
        return True if the group can create a village: it must carry enough
        resources and have at least one woman
        """
        #TODO
        return True

    def update(self):
        self.village.update()

    def as_li(self):
        return render_to_string(
                'game/group_li.html',
                {'group': self},
                )

    def can_split(self, units_dict):
        """Check if the group can split the instructed way"""
        stacks = self.unitstack_set.values_list('unit_type', 'number')
        c_own_stacks = Counter({a:b for (a,b) in stacks})
        c_other_stacks = Counter({a:b for (a,b) in units_dict})
        diff = c_own_stacks.subtract(c_other_stacks)
        for i in diff.values():
            if i < 0:
                return False
        return True



    @transaction.commit_on_success
    def split(self, units_dict):
        """
        Split the group in two according to the units_dict that
        countains the new group’s composition.
        If units_dict countains to many units for any unit type
        according to the original group, raises CannotSplit.
        """
        new_group = Group(
                resources=Resources(),
                village=self.village,
                position=self.position,
                )
        stacks = self.unitstack_set.all()
        #if the number of units in the new group is more than in the old
        #group, then we shouldn't split.
        #TODO more user-friendly message
        total_number = sum(units_dict.values())
        if total_number == 0:
            return None
        #TODO improve over-crowded new group handling
        elif sum([stack.number for stack in stacks]) < total_number:
            raise self.CannotSplit
        elif sum([stack.number for stack in stacks]) == total_number:
            return self
        for unit_type_id, number in units_dict.iteritems():
            try:
                stack = stacks.get(unit_type_id=unit_type_id)
            except UnitStack.DoesNotExist:
                raise self.CannotSplit
            if number > 0:
                if stack.number >= number:
                    new_group.id or new_group.save()
                    UnitStack.objects.create(
                            unit_type_id=unit_type_id,
                            group=new_group,
                            number=number,
                            )
                    if number == stack.number:
                        stack.delete()
                    else:
                        stack.number -= number
                        stack.save()
                else:
                    raise self.CannotSplit
        try:
            self.gathering
            self.position.compute_gathering_production()
        except Gathering.DoesNotExist:
            pass

        return new_group

    def log_report(self, *args, **kwargs):
        return self.village.log_report(*args, **kwargs)

    def flee(self):
        "When a group is defeated, it flees back to its origin village"
        stacks = self.stacks_to_list()
        self.village.plan_flee_return(stacks)
        self.delete()

    def meet_friends(self):
        """if a friendly village or aimless group is in the same tile,
        the groups will merge"""
        try:
            village = choice(self.get_tribe().village_set.filter(
                    position=self.position))
            village.add_inhabitants(self)
        except IndexError:
            try:
                group = self.get_tribe().get_all_groups()\
                        .filter(position=self.position)\
                        .get(mission=None)
                self.merge(group)
            except Group.DoesNotExist:
                pass

    def delete(self):
        village = self.village
        res = super(Group, self).delete()
        village.update_income()
        village.plan_next_starvation()
        self.resources.delete()
        return res

    def capture_village(self, village):
        village.delegate_all_groups()
        village.tribe = self.get_tribe()
        village.set_inhabitants(self)


#Troupeau ;)
class Herd(models.Model, GroupManagementMixin):
    position = models.OneToOneField('Tile')
    
    class Meta:
        app_label = 'game'

    @staticmethod
    def create_herd():
        "create a herd at random"
        #TODO
