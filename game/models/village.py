#!vim: set fileencoding=utf-8 :

from ..utils.exceptions import CannotPay, TechnologyNeeded
from game import tasks
from building import ConstructedBuilding
from celery.task.control import revoke
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from game.utils.constants import STARVATION_LIMIT, INIT_TRIBE_RESOURCES
from group import Group, UnitStack
from maps import Carte
from resources import Resources, Cost
from technology import TechnologyKnowledge
from virtuals import UnitCreation, TechnologyResearch
import logging
import random


logger = logging.getLogger(__name__)

class BuildingVillageOnLakeException(Exception):
    logger.warning("trying to build a village in a lake")

class Village(models.Model):
    """
    A village is caracterized by its position on the :model:`game.Map` and
    its :model:`game.Tribe`. It also provides data about stocks, inhabitants,
    name. Management methods are available.
    """
    name = models.CharField(max_length=50, null=False, blank=False)
    inhabitants = models.OneToOneField(
            Group, blank=True, null=True,
            related_name='inhabitants_of',
            editable=False)
    resources = models.OneToOneField(
            'Resources',
            on_delete=models.PROTECT)
    date_creation = models.DateTimeField(auto_now_add=True)
    fertility = models.PositiveSmallIntegerField(default=0)
    tribe = models.ForeignKey('Tribe')
    position = models.ForeignKey('Tile')
    resources_last_update = models.DateTimeField(auto_now_add=True)
    fertility_last_update = models.DateTimeField(auto_now_add=True)
    income = models.OneToOneField(
            'Resources',
            related_name='village_income',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            )
    starvation_task_id = models.CharField(max_length=64, null=True, editable=False)

    class Meta:
        app_label = 'game'
        ordering = ['date_creation']

    def delete(self):
        self.resources.delete()
        self.income.delete()
        return super(Village, self).delete()

    def __unicode__(self):
        return 'Village {}'.format(
                self.id,
                )

    def set_inhabitants(self, group):
        self.inhabitants = group
        v = group.village
        if v is None or v.id <> self.id:
            group.village_id = self.id
            group.save()
            self.update_income()
            if v is not None:
                v.update_income()
        self.save()

    def add_inhabitants(self, group):
        if self.inhabitants:
            self.inhabitants.merge(group)
        else:
            self.set_inhabitants(group)
        self.update_income()

    def create_unit(self, unit):
        if not self.inhabitants:
            inhab = Group.objects.create()
            inhab.add_unit([(unit.identifier, 1)])
            inhab.position_id = self.position_id
            inhab.save()
            self.set_inhabitants(inhab)
        else:
            self.inhabitants.add_unit([(unit.identifier, 1)])
            self.update_income()

    def add_unit_creation(self, unittype, number=1):
        """
        Create a new :model:`tribe.UnitCreation` for the considered
        village, adding automatically the order and maybe the date_begin
        fields. This function also checks if the tribe has the needed technos
        and if it can pay, raising errors otherwise.

        **Arguments**
            `unittype`:
                the `tribe.UnitType` object representing the new units

            `number`:
                specifies the number of units the player wants to create.
                Values 1 by default

        **Raise**
            `CannotPay`
            `TechnologyNeeded`

        """
        c = self.tribe.unit_limiting_techno(unittype)
        if c:
            raise TechnologyNeeded(c.most_common(1)[0][0])
        self.pay(unittype.cost * number)
        UnitCreation.add_unit_creation(
                unittype=unittype,
                village=self,
                number=number,
                )

    @staticmethod
    def create_village( tribe,
                        name='New village',
                        tile=None,
                        first=False,
                        ):
        #TODO select the right map
        if tile is None:
            position = Carte.objects.all()[0]\
                    .get_free_village_position()
        else:
            position = tile
        if position.ground == 3:
            raise BuildingVillageOnLakeException
        #TODO set the right resources
        if first:
            resources = Resources.objects.create(
                    wood=INIT_TRIBE_RESOURCES['wood'],
                    food=INIT_TRIBE_RESOURCES['food'],
                    silex=INIT_TRIBE_RESOURCES['silex'],
                    skin=INIT_TRIBE_RESOURCES['skin'],
                    )
        else:
            resources = Resources.objects.create()
        village = Village.objects.create(
                name=name,
                resources=resources,
                tribe=tribe,
                position=position,
                )
        return village

    def can_pay(self, cost):
        max_cost = Cost(
                    resources=self.resources,
                    divinity=self.tribe.divinity,
                    fertility=self.fertility,
                    )
        return max_cost.can_pay(cost)

    def pay(self, cost):
        """raises CannotPay if the village does not have
        enough resources"""
        if self.can_pay(cost):
            self.resources -= cost.resources
            self.resources.save()
            
            self.tribe.divinity -= cost.divinity
            self.tribe.save()
            
            self.fertility -= cost.fertility
            self.save()
        else:
            raise CannotPay

    def get_total_unit_number(self):
        """ The total number of units in all the groups depending on the village"""
        all_stacks = UnitStack.objects.filter(group__village=self)
        return sum([stack.number for stack in all_stacks])

    def get_food_consumption(self):
        """
        Calcule la consumption horaire de food
        en prenant en compte tous les hommes du village
        """
        residents = UnitStack.objects.filter(group__village=self)
        # TODO
        #Ici le number de requêtes SQL est réductible lors que plusieurs
        #groups différents contiennent le même type d’unités. À voir dans
        #la doc django avec les mises en cache
        result = 0
        for stack in residents:
            result += stack.number * stack.unit_type.human.consumption
        return result

    def get_income(self):
        """
        Compute the positive income of the village, considering the gatherings.

        **Return**
        :model:`tribe.Resources`

        """
        current_gatherings = self.gathering_set.all()
        result = Resources()
        for gathering in current_gatherings:
            setattr(result, gathering.resource,  getattr(result, gathering.resource)+gathering.production)
        return result

    def update_income(self):
        """
        Get the income of the :model:`tribe.Village`.get_income function
        and take the food consumption over. Store it in the database.
        Calls the :model:`tribe.Village`.plan_next_starvation function.

        **Return**
        Nothing.

        """
        raw_income = self.get_income()
        raw_income.food -= self.get_food_consumption()
        raw_income.save()
        self.income = raw_income
        self.plan_next_starvation()
        self.save()

    def get_fertility_increase(self):
        """
        Calcule la fertilité horaire d’un village

        Hardcode des unités productrices de fertilité
        """
        if not self.inhabitants_id:
            return 0
        fertility_producers = self.inhabitants.unitstack_set.all()\
                .filter(Q(unit_type__name__iexact='femme') \
                    | Q(unit_type__name__iexact='guerisseuse'))

        result = 0
        for stack in fertility_producers:
            if stack.unit_type.identifier == 'woman':
                result += stack.number
            else:
                result += 2 * stack.number
        return result

    def choose_a_stack(self):
        """
        Choose a :model:`tribe.Unitstack` object amoung all those supported
        by the :model:`tribe.Village` at random, considering the number of
        soldiers in all of them
        """
        all_stacks = UnitStack.objects\
                .filter(group__village=self)
        chosen = random.randint(0, self.get_total_unit_number())
        for stack in all_stacks:
            if stack.number > chosen:
                break
            chosen -= stack.number
        return stack

    def kill_one_guy(self):
        """
        Choose one soldier at random amoung those supported by the
        village, for he to be eaten by his friends so they are happy
        """
        stack = self.choose_a_stack()
        if stack.number == 1:
            #TODO dont kill the last inhabitant of the village
            stack.group.unitstack_set.count() == 1 and stack.group.delete()
            stack.delete()
        else:
            stack.number -= 1
            stack.save()
        self.resources.food += 50   #TODO
        self.resources.save()
        self.update_income()
        return stack.unit_type

    def plan_next_starvation(self):
        """
        If the food income in a village is negative, compute the
        date of the starvation and plans a call to check_starvation
        for this date
        """
        logger.info("planning next starvation")
        if self.starvation_task_id:
            revoke(self.starvation_task_id) 
            logger.info("found old starvation task -- revoking")
        if self.income.food < 0:
            logger.info("negative income. computing starvation time")
            next_starvation_delta =\
                    (STARVATION_LIMIT - float(self.resources.food))\
                    / float(self.income.food)
            countdown = (next_starvation_delta * 3600).__int__()
            logger.info("planning next starvation time for village {}"
                    ". countdown : {}".format(self.id, countdown))
            res = tasks.check_starvation.apply_async(
                    args=[self.id],
                    countdown=countdown,
                    )
            self.starvation_task_id = res.id
            self.save()
        else:
            logger.info("positive income. No planned starvation")

    def resources_update(self):
        """
        Met à jour les réserves du village, spécialement de
        food afin que l’on puisse déterminer si des
        hommes meurent de faim. Ne calcule pas les revenus !

        Automatiquement appelé par le décorateur
        @resources_update_required
        """
        delta_since_update = timezone.now() - self.resources_last_update
        in_hours = delta_since_update.total_seconds() / 3600
        try:
            self.resources += (self.income * in_hours)
        except TypeError:           # if self.income is null
            self.update_income()
            self.resources += (self.income * in_hours)
        self.fertility += (self.get_fertility_increase() * in_hours)
        self.resources_last_update = timezone.now()
        self.save(update_fields=['fertility', 'resources_last_update'])
        self.resources.save()
        self.tribe.divinity_update()

    def max_resources_storage(self):
        " Resources object with the max storage values "
        return Resources(food=2000, wood=2000, silex=2000, skin=2000)

    def receive_resources(self, resources):
        """
        add the resources to the village
        create a new object resources with this values and return it
        """
        max_resources = self.max_resources_storage()
        transfered_resources = Resources(
            food=min(
                resources.food,
                max_resources.food - int(self.resources.food),
                ),
            wood=min(
                resources.wood,
                max_resources.wood - int(self.resources.wood),
                ),
            silex=min(
                resources.silex,
                max_resources.silex - int(self.resources.silex),
                ),
            skin=min(
                resources.skin,
                max_resources.skin - int(self.resources.skin),
                ),
        )
        #need to create a new instance of resources to remember for the report
        transfered_resources.pk = None
        transfered_resources.save()
        self.resources += transfered_resources
        self.resources.save()
        self.plan_next_starvation()
        return transfered_resources

    def resources_html(self):
        """A handy way to quickly insert the
        village resources into templates"""
        resources = [
                        (k, (v, self.income.to_dict().get(k)))
                        for k,v in self.resources.to_dict().items()
                    ]
        resources.append(
                    (
                    'fertility',
                    (self.fertility, self.get_fertility_increase()),
                    )
                )
        return render_to_string(
                'game/village_resources.html',
                {
                    'resources': resources
                },
                )

    def research_techno(self, techno):
        """
        Start a techno research if the prerequisites are satisfied
        and if the village can pay

        **raises**
            `CannotPay`
            `TechnologyNeeded`
        """
        try:
            next_level = self.tribe\
                    .technologyknowledge_set\
                    .get(technology=techno)\
                    .level + 1
        except TechnologyKnowledge.DoesNotExist:
            next_level = 1

        cost = techno.research_cost(next_level)
        a = self.tribe.limiting_techno(techno)
        if a:
            raise TechnologyNeeded(a.most_common(1)[0][0])
        self.pay(cost)
        TechnologyResearch.add_techno_research(techno, self.tribe)
        
    def building_cost_next_level(self, building):
        """
        Gives the cost to build the next level of this kind of builing
        """
        try:
            return ConstructedBuilding.objects.get(building=building, village=self).cost_next_upgrade()
        except ConstructedBuilding.DoesNotExist:
            return building.cost

    def plan_flee_return(self, stacks):
        return_time = 10    #TODO
        tasks.flee_return_task.apply_async(
                    args=[self.id, stacks],
                    #TODO
                    countdown=return_time,
                )


    def log_report(self, type, subject, body):
        report = self.tribe.log_report(type, subject, body)
        report.village = self
        report.save()
        return report

    def delegate_all_groups(self):
        """attach all the groups of the village to another village.
        
        This is useful when the village is captured or the user
        wants to delete it
        """
        village = self.tribe.village_set.all()[0]
        for group in self.group_set.all():
            group.village_id = village.id
            group.save()
        village.update()
