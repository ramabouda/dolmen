#vim: set fileencoding=utf-8 :

from celery.task.control import revoke
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from game.utils.combat import Combat
from game.utils.constants import VILLAGE_CREATION_NEEDED_RESOURCES, NB_VILLAGES_PER_TILE
from group import Group, Herd
from resources import Gathering, Resources
from game import tasks
from village import Village
import datetime

#also used in serializers/mission.py
MISSION_CHOICES = (
        ('gather', 'récolter'),
        ('hunt', 'hunt'),
        ('attack', 'attack'),
        ('loot', 'loot'),
        ('annex', 'annex'),
        ('move', 'move'),
        ('carry', 'carry'),
        ('found', 'found'),
        ('meet', 'meet'),
        ('return', 'return'),
        )


class RouteElement(models.Model):
    """
    Rank = 0 for the origin tile
    Rank = n for the destination tile
    """
    mission = models.ForeignKey('Mission')
    tile = models.ForeignKey('Tile')
    rank = models.SmallIntegerField()

    class Meta:
        app_label = 'game'
        ordering = ['rank']


class Mission(models.Model):
    """
    A mission is basically a path, a target
    and a mission_type. The corresponding group
    will walk through the path, achieve its mission
    and, depending on its type, go back to its origin
    """
    group = models.OneToOneField(Group)
    mission_type = models.CharField(max_length=15, choices=MISSION_CHOICES)
    date_begin = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)
    date_next_move = models.DateTimeField(blank=True, null=True)
    task_id = models.CharField(
            max_length=64,
            blank=True,
            null=True,
            editable=False,
            )
    route = models.ManyToManyField(
            'Tile',
            through='RouteElement',
            null=True,
            blank=True,
            )
    # la cible éventuelle de l'action sous forme d’un id. Si l’action est
    # attack, ce sera l’id d’un group, si l’action est hunt, ce sera
    # un troupeau etc. À noter le cas de gather où target_id renvoie
    # à un objet Gather
    target_id = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        app_label = 'game'

    def delete(self):
        if self.task_id:
            revoke(self.task_id)
        if self.mission_type == 'gather' and self.target_id:
            self.get_target().delete()
        return super(Mission, self).delete()

    @staticmethod
    def start_mission(group=None, route=None, mission_type='move', target_id=None, split_group=None):
        """
        Here a path is an ordered list of tiles ids, with the
        current position of the group first.
        """
        if group is None or route is None:
            raise ValueError("group and route cannot be null")
        try:
            village = group.inhabitants_of
            village.inhabitants_id = None
            village.save()
        except Village.DoesNotExist:
            pass
        try:
            group.mission.delete()
        except Mission.DoesNotExist:
            pass
        #except AssertionError:
            ##django rest framework creates a mission object while deserializing
            ##but this object is not saved, so it creates an assertion error
            ##when deleted
            #pass
        m = Mission.objects.create(
                group=group,
                mission_type=mission_type,
                target_id=target_id,
                )
        # FIXME we should remove first case once dajaxice is forgotten
        if isinstance(route[0], int):
            for tile in route:
                RouteElement.objects.create(
                        mission=m,
                        tile_id=tile,
                        rank=route.index(tile),
                        )
        else:
            for tile in route:
                RouteElement.objects.create(
                        mission=m,
                        tile=tile,
                        rank=route.index(tile),
                        )
        eta=m.compute_date_next_move()
        res = tasks.progress.apply_async(
                args=[m.id],
                eta=eta,
                )
        m.date_next_move = eta
        m.task_id = res.id
        m.save()
        return m

    def get_next_tile(self):
        tile = self.group.position
        rank_case = RouteElement\
                .objects\
                .filter(mission=self)\
                .get(tile=tile)\
                .rank
        try:
            return self.routeelement_set.get(rank=rank_case + 1).tile
        except models.exceptions.ObjectDoesNotExist:
            return None

    def come_back(self):
        i = 0
        for element in RouteElement\
                .objects\
                .filter(mission=self)\
                .order_by('-rank'):
            element.rank = i
            element.save()
            i += 1
        self.mission_type = 'return'           
        eta = self.compute_date_next_move()
        res = tasks.progress.apply_async(
                args=[self.id],
                eta=eta,
                )
        self.date_next_move = eta
        self.task_id = res.id
        self.save()

    def get_target(self):
        cases = {
                'hunt': lambda id: Herd.objects.get(id=id),
                'attack': lambda id: Group.objects.get(id=id),
                'loot': lambda id: Village.objects.get(id=id),
                'annex': lambda id: Village.objects.get(id=id),
                'carry': lambda id: Village.objects.get(id=id),
                'meet': lambda id: Village.objects.get(id=id),
                'gather': lambda id: Gathering.objects.get(id=id),
                'move': lambda id: None,
                }
        return cases[self.mission_type](self.target_id)

    def achieve_mission_move(self):
        self.group.log_report(
                type=10,
                subject=self.get_report_subject(),
                body=self.get_report_body(),
                )
        self.task_id = None
        self.group.meet_friends()
        self.delete()

    def achieve_mission_return(self):
        self.group.log_report(
                type=10,
                subject=self.get_report_subject(),
                body=self.get_report_body(),
                )
        self.task_id = None
        self.group.meet_friends()
        self.delete()

    def achieve_mission_gather(self):
        a = Gathering.add_gathering(self.group)
        self.target_id = a.id
        self.save()

    def achieve_mission_hunt(self):
        # TODO
        pass

    def achieve_mission_attack(self):
        target = self.get_target()
        if target.position_id <> self.group.position_id:
            self.group.log_report(
                type=1,
                subject="Votre attaque n’a pas abouti",
                body="La cible n'était pas à l'endroit prévu",
            )
            return
        combat = Combat(self.group, target)
        success = combat.is_attacker_winner()

        self.group.log_report(
                type=1,
                subject='Votre attaque a été menée à bien',
                body=combat.report,
                )
        target.log_report(
                type=1,
                subject='Votre groupe a été attaqué',
                body=combat.report,
                )

        #FIXME optimize sql requests
        for unittype in combat.attack_deads:
            stack = self.group.unitstack_set.get(unit_type=unittype)
            stack.kill_guys(combat.attack_deads[unittype])
        for unittype in combat.defense_deads:
            stack = target.unitstack_set.get(unit_type=unittype)
            stack.kill_guys(combat.defense_deads[unittype])

        if success:
            self.group.steal(target)
            if target.units_number() == 0:
                target.delete()
            else:
                target.flee()
            self.come_back()
            return
        elif success is None:
            if target.units_number() == 0:
                target.delete()
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.come_back()
            return
        else:
            target.steal(self.group)
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.group.flee()
            return

    def achieve_mission_carry(self):
        #transfert
        target_village = Village.objects.get(pk=self.target_id)
        transfered_resources = target_village.receive_resources(self.group.resources)
        self.group.resources -= transfered_resources

        #-- report
        #FIXME html and complete reports
        #report for the target if not himself
        if(self.group.village.tribe != target_village.tribe):
            target_village.log_report(
                    type=10,#TODO
                    subject='De nouvelles ressources ont été apportées',
                    body='Des ressources en provenance du village {},'
                        'appartenant à la tribu {}'
                        'sont arrivées dans votre village {}.'\
                            .format(
                                self.group.village,
                                self.group.get_tribe(),
                                target_village,
                                ),
                            )
        #report for himself
        context = {
                'village_origin': self.group.village,
                'village_destination': target_village,
                }
        self.group.log_report(
                    type=10,#TODO
                    subject=self.get_report_subject(context),
                    body=self.get_report_body(context),
                    )
        self.come_back()

    def achieve_mission_loot(self):
        target = self.get_target()
        opponents = target.inhabitants
        if target.position_id <> self.group.position_id:
            self.group.log_report(
                type=1,
                subject="Votre attaque n’a pas abouti",
                body="La cible n'était pas à l'endroit prévu",
            )
            return
        combat = Combat(self.group, opponents)
        success = combat.is_attacker_winner()

        self.group.log_report(
                type=1,
                subject='Votre attaque a bien eu lieu',
                body=combat.report,
                )
        target.log_report(
                type=1,
                subject='Votre attaque a échoué lamentablement',
                body=combat.report,
                )

        #FIXME optimize sql requests
        for unittype in combat.attack_deads:
            stack = self.group.unitstack_set.get(unit_type=unittype)
            stack.kill_guys(combat.attack_deads[unittype])
        for unittype in combat.defense_deads:
            stack = opponents.unitstack_set.get(unit_type=unittype)
            stack.kill_guys(combat.defense_deads[unittype])

        if success:
            self.group.steal(target)
            opponents.flee()
 #           if target.units_number() == 0:
 #               target.delete()
 #           else:
 #               target.flee()
 #           self.come_back()
            return
        elif success is None:
            if opponents.units_number() == 0:
                opponents.delete()
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.come_back()
            return
        else:
            target.steal(self.group)
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.group.flee()
            return

    def achieve_mission_annex(self):
        target = self.get_target()
        opponents = target.inhabitants
        if target.position_id <> self.group.position_id:
            self.group.log_report(
                type=1,
                subject="Votre attaque n’a pas abouti",
                body="La cible n'était pas à l'endroit prévu",
            )
            return
        combat = Combat(self.group, opponents)
        success = combat.is_attacker_winner()

        self.group.log_report(
                type=1,
                subject='Votre attaque a bien eu lieu',
                body=combat.report,
                )
        target.log_report(
                type=1,
                subject='Votre attaque a échoué lamentablement',
                body=combat.report,
                )

        #FIXME optimize sql requests
        for unittype in combat.attack_deads:
            stack = self.group.unitstack_set.get(unit_type=unittype)
            stack.kill_guys(combat.attack_deads[unittype])

        if success:
            opponents.delete()
            target.tribe = self.group.get_tribe()
            target.add_inhabitants(self.group)
            target.save()
 #           if target.units_number() == 0:
 #               target.delete()
 #           else:
 #               target.flee()
 #           self.come_back()
            return
        elif success is None:
            for unittype in combat.defense_deads:
                stack = opponents.unitstack_set.get(unit_type=unittype)
                stack.kill_guys(combat.defense_deads[unittype])
            if opponents.units_number() == 0:
                opponents.delete()
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.come_back()
            return
        else:
            for unittype in combat.defense_deads:
                stack = opponents.unitstack_set.get(unit_type=unittype)
                stack.kill_guys(combat.defense_deads[unittype])
                target.steal(self.group)
            if self.group.units_number() == 0:
                self.group.delete()
            else:
                self.group.flee()
            return
        # TODO
        pass

    def achieve_mission_found(self):
        if not self.group.resources or\
                self.group.position.village_set.count() >= NB_VILLAGES_PER_TILE\
                or self.group.resources <\
                Resources.dict_to_resources(VILLAGE_CREATION_NEEDED_RESOURCES):
            self.come_back()
            self.group.log_report(
                    type=11,
                    subject='Impossible de créer le village',
                    body='Tous les emplacements de la case'
                        ' sélectionnée sont occupés ou bien '
                        'vous ne disposez pas de suffisamment de ressources',
                    )
        v = Village(
                name="New village",
                inhabitants=self.group,
                resources=Resources.objects.create(),
                tribe=self.group.village.tribe,
                position=self.group.position,
                )
        v.resources.save()
        v.save()
        v.update_income()
        self.group.village = v
        self.group.save()
        update_resources = v.receive_resources(self.group.resources)
        update_resources.save()
        self.group.resources = update_resources
        self.group.resources -= v.receive_resources(self.group.ressources)
        self.group.resources.save()

    def get_report_subject(self, context={}):
        return render_to_string(
                'game/reports/mission_{}_subject.html'.format(self.mission_type),
                context,
                )

    def get_report_body(self, context={}):
        return render_to_string(
                'game/reports/mission_{}_body.html'.format(self.mission_type),
                context,
                )

    def __unicode__(self):
        return self.mission_type

    def compute_date_next_move(self):
        if self.get_next_tile() == None:
            diff = self.group.get_internal_move_delay()
        else:
            diff = self.group.get_cross_delay(self.group.position)
        if self.date_next_move:
            return self.date_next_move + datetime.timedelta(seconds=diff)
        else:
            return timezone.now() + datetime.timedelta(seconds=diff)

