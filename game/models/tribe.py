#!vim: set fileencoding=utf-8 :

from collections import Counter
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from group import Group, UnitStack
from maps import Tile
from report import Report
from resources import Resources
from technology import TechnologyKnowledge, Technology, Requirement
from unit import UnitType
from village import Village
from game.utils.constants import INIT_TRIBE_RESOURCES, INIT_TRIBE_UNITS




class Tribe(models.Model):
    """
    Store the information about a tribe, which will
    basically be used as a foreign key for some
    :model:`game.Village`s. It is also used for
    features such as technologies (see
    :model:`game.Technology`), alliances (:model:`game.Alliance`),
    friendship,
    basic history and so on.
    """
    name = models.CharField(max_length=25, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL)
    #obligatoire, pas encore bien défini
    #upload_to
    emblem = models.FileField(upload_to='/', null=True, blank=True)
    divinity = models.DecimalField(
            default=0,
            max_digits=7,
            decimal_places=2,
            )
    divinity_income = models.DecimalField(
            default=0,
            max_digits=7,
            decimal_places=2,
            )
    divinity_last_update = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    grade = models.ForeignKey('Grade', null=True, blank=True)
    alliance = models.ForeignKey('Alliance', null=True, blank=True)

    techno_levels = {}
    technos = None

    class Meta:
        app_label = 'game'
        permissions = (
                ('can_have_several_tribes',
                    'Peut posséder plusieurs tribes'),
                )

    def __unicode__(self):
        return self.name

    def increase_tech_level(self, techno):
        """
        Increase the level of the corresponding
        :model:`game.TechnologyKnowledge`
        if available. Otherwise creates it and set
        the level to 1.
        **Param**
        ``techo``
            a :model:`game.Technology` object
        """
        try:
            knowledge = self\
                    .technologyknowledge_set\
                    .get(technology=techno)
            knowledge.level += 1
            knowledge.save()
        except TechnologyKnowledge.DoesNotExist:
            knowledge = self\
                    .technologyknowledge_set\
                    .create(technology=techno)

    def get_research_duration(self, tech):
        """
        Calcule la durée nécessaire au développement
        d’une technology à un certain level
        pour la tribe concernée. Retourne le temps
        nécessaire en secondes.
        """
        if settings.FAST_RESEARCH:
            return 10
        try:
            knowledge = self.technologyknowledge_set.get(technology=tech)
            cost = knowledge.cost_next_upgrade()
        except ObjectDoesNotExist:
            cost = tech.cost
        resources_amount = sum([cost.resources[i] for i in cost.resources])
        return resources_amount*180


    def limiting_techno(self, techno):
        """
        Check if the prerequisites to purchase a technology
        are fulfilled.
        
        **Return**
        a Counter object, representing the missing technos
        """
        required = techno.need.values_list('need', 'level_required')
        knowledges = self.technologyknowledge_set.values_list('technology', 'level')
        #do we already know the techno? At which level?
        l = filter(lambda x: x[0] == techno.id, knowledges)
            
        creq = Counter({a:b for (a,b) in required})
        cknow = Counter({a:b for (a,b) in knowledges})
        if l:
            level = l[0][1]
            for k in creq.keys():
                creq[k] += level
        return creq - cknow

    def unit_limiting_techno(self, unit_type):
        """
        check if the prerequisites to enroll a unit are fulfilled

        **Return**
        a Counter object, representing the missing technos
        """
        required = unit_type.unitrequirement_set.values_list('need', 'level_required')
        knowledges = self.technologyknowledge_set.values_list('technology', 'level')
        creq = Counter({a:b for (a,b) in required})
        cknow = Counter({a:b for (a,b) in knowledges})
        return creq - cknow

    @staticmethod
    def create_tribe(name, user, carte):
        """
        Initialise une tribe (à utiliser après la création d'un compte)

        """
        tribe = Tribe(name=name, leader=user)
        tribe.save()

        resources_initiales = Resources(
                wood=INIT_TRIBE_RESOURCES['wood'],
                food=INIT_TRIBE_RESOURCES['food'],
                silex=INIT_TRIBE_RESOURCES['silex'],
                skin=INIT_TRIBE_RESOURCES['skin']
                )

        resources_initiales.save()
        village = Village.create_village(tribe, first=True)

        inhabitants = Group.objects.create(
                position=village.position,
                village=village,
                )
        village.inhabitants = inhabitants
        for key in INIT_TRIBE_UNITS:
            new_pile = UnitStack(
                    unit_type=UnitType.objects.get(identifier__iexact=key),
                    group=inhabitants,
                    number=INIT_TRIBE_UNITS[key],
                    )
            new_pile.save()
        village.update_income()

        return tribe


    def get_reachable_technos(self):
        """
        gives back the technos that the tribe is able to research
        or already has discovered and the set of the IDs of the technos
        whose requirements are achieved but the needed technology are not
        to a higher level than the current level of the target’s knowledge

        DON’T USE THIS if you need to check if the tribe can research one
        single techno
        """
        knowledges = self.technologyknowledge_set.values('technology', 'level')
        unreachable_technos = set()
        requirements = Requirement.objects.values('level_required', 'need', 'target')

        knowledges_dict = {a['technology']: a['level'] for a in knowledges}

        requirement_level_not_improved = set()

        for requirement in requirements:
            requirement_ok = False
            for knowledge in knowledges:
                if requirement['need'] == knowledge['technology']\
                        and requirement['level_required'] <= knowledge['level']:
                    requirement_ok = True
                    if requirement['target'] in knowledges_dict\
                            and knowledges_dict[requirement['need']] < knowledges_dict[requirement['target']] + 1:
                        requirement_level_not_improved.add(requirement['target'])
                    break

            if not requirement_ok:
                unreachable_technos.add(requirement['target'])
        requirement_level_not_improved = requirement_level_not_improved.difference(unreachable_technos)
        a = list(unreachable_technos)
        reachable_technos = Technology.objects.exclude(id__in=a)
        return reachable_technos, requirement_level_not_improved

    def get_reachable_units(self):
        #TODO and implement technological requirements
        raise NotImplementedError


    def get_techno_level_by_name(self, techno_identifier):
        """
        returns the techno level corresponding to the techno_identifier
        for this tribe
        """
        self.get_technos()
        try:
            #tech_level = self.techno_levels[techno_identifier]
            tech_level = self.technos.get(technology__identifier=techno_identifier).level
        except TechnologyKnowledge.DoesNotExist:
            tech_level = 0
        return tech_level


    def get_technos(self, force_update=False):
        """
        complete the self.techno_levels dict, and returns it
        force_update allows you to force a new query to the DB
        """

        if force_update or self.technos == None:
            self.technos = self.technologyknowledge_set.all()

        return self.technos


    def update_divinity_income(self):
        """ return the income in divinity points """
        techno_points = float(
                (self.get_techno_level_by_name('pictorial_art') + \
                    self.get_techno_level_by_name('sculpture') + \
                    self.get_techno_level_by_name('funeral_rite')\
                )) * 10 / 24

        #TODO
        adoration_points = 0

        self.divinity_income = techno_points + adoration_points
        return self.divinity_income


    def divinity_update(self):
        """update the amont of divinity_points"""
        delta_since_update = timezone.now() - self.divinity_last_update
        in_hours = delta_since_update.total_seconds() / 3600
        self.divinity_last_update = timezone.now()
        self.divinity += self.divinity_income * Decimal(in_hours)
        self.save(update_fields=['divinity_last_update', 'divinity'])

    def get_all_groups(self):
        return Group.objects.filter(
                village__in=self.village_set.all()
                )

    def get_carte(self):
        return self.village_set.all()[0].position.carte

    def get_all_groups_positions(self):
        """
        Return a querySet corresponding to the cases in which the
        tribe has a group
        """
        #FIXME is it efficient?
        return Tile.objects.filter(
                group__in=self.get_all_groups()
                ).distinct()
 
    def get_seen_cases(self, group_positions=None):
        """
        Return the cases the tribe can see, that is to say the cases
        distant by no more than 1 from a group of the tribe.
        As an optional argument, group_positions can be given as a
        querySet that corresponds to the result of get_all_groups_positions
        to avoid redoundant computations.
        """
        #TODO select only the correct map
        if group_positions is None:
            group_positions = self.get_all_groups_positions()
        if not group_positions.exists():
            return Tile.objects.none()
        
        filters = Q()
        for tile in group_positions:
            filters = filters | (Q(x__range=(tile.x - 1, tile.x + 1))
                    & Q(y__range=(tile.y - 1, tile.y + 1))
                    & Q(z__range=(tile.z - 1, tile.z + 1))
                    )
        return Tile.objects.filter(filters).distinct()
 
    def get_unseen_cases(self, seen_cases=None):
        """get the :model:`game.Tile`s that the tribe cannot see"""
        carte = self.get_carte()
        if seen_cases is None:
            seen_cases = self.get_seen_cases()
        return Tile.objects.filter(carte=carte).exclude(id__in=seen_cases)
    
    def get_all_tiles(self):
        carte = self.get_carte()
        return Tile.objects.filter(carte = carte)

    def get_village_positions(self):
        return Tile.objects.filter(
                    village__in=self.village_set.all()
                ).distinct()
    
    def dispatch_tiles(self):
        """dipatch the tiles into a dict with the
        'seen' and 'unseen' keys, plus a bonus
        'gpositions' one and a 'vpositions' one.
        """
        gpositions = self.get_all_groups_positions()
        vpositions = self.get_village_positions()
        seen_tiles = self.get_seen_cases(group_positions=gpositions)
        unseen_tiles = self.get_unseen_cases(seen_cases=seen_tiles)
        all_tiles = self.get_all_tiles()
        return {
                'groups': gpositions,
                'villages': vpositions,
                'seen': seen_tiles,
                'unseen': unseen_tiles,
                'all': all_tiles
                }

    def get_serialized_tiles(self):
        from ..serializers import TileRendererSerializer
        dicto = self.dispatch_tiles()
        result = TileRendererSerializer(
                dicto['seen'], many=True).data

        for item in result:
            item['seen'] = True

        result2 = TileRendererSerializer(
                dicto['unseen'], many=True,).data
        for item in result2:
            item['seen'] = False
        result.extend(result2)
        return result

    def get_serialized_groups(self):
        #from ..serializers import GroupSerializer
        #groups = self.get_all_groups()
        #TODO
        raise NotImplementedError

    def get_unread_messages(self):
        """
        return a queryset corresponding to the threads
        which at least one message is unread by the tribe
        """
        try:
            from messages import Message
            query = Message.objects\
                    .filter(thread__in=self.received_thread.all())\
                    .exclude(readers__id=self.id)
        except ObjectDoesNotExist:
            query = None
        return query

    def get_unread_threads(self):
        try:
            query = self.received_thread\
                    .exclude(message__readers__id=self.id)
        except ObjectDoesNotExist:
            query = None
        return query

    def log_report(self, type, subject, body):
        return Report.objects.create(
                type=type,
                tribe=self,
                subject=subject,
                body=body,
                )

    def unread_reports_number(self):
        return self.report_set.filter(read=False).count()
