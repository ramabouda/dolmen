#vim: set fileencoding=utf-8 :

from celery import task
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from utils.constants import STARVATION_LIMIT
import logging

logger = logging.getLogger(__name__)

@task
def check_starvation(village_id):
    """
    check if the village is in starvation (ie if the food reserve
    is too low). In this tile, call the kill_one_guy function and
    calls itself for the next starvation time.
    """
    from models import Village
    village = Village.objects.get(id=village_id)
    village.resources_update()
    if village.resources.food <= STARVATION_LIMIT:
        logger.info("village {} in starvation. killing one unit".format(village_id))
        village.kill_one_guy()
        village.log_report(type=0, subject="Famine !",
                body="votre village {} est en famine. L'une de ses unités a"
                " été dévorée par ses compagnons affamés".format(village.name))
        village.starvation_task_id = ''
        village.plan_next_starvation()

@task
def flee_return_task(village_id, stacks):
    from models import Village, Group
    village = Village.objects.get(id=village_id)
    if village.inhabitants_id:
        village.inhabitants.add_unit(stacks)
        village.plan_next_starvation()
    else:
        group = Group.objects.create(village_id=village_id)
        group.add_unit(stacks)
        group.save()
        village.set_inhabitants(group)

@task
def achieve_enroll(unit_creation_id):
    from models import UnitCreation
    unit_creation = UnitCreation.objects.get(id=unit_creation_id)
    unit_creation.village.create_unit(unit_creation.unit)
    try:
        unit_creation.next_creation.date_begin = timezone.now()
        unit_creation.next_creation.save()
        achieve_enroll.apply_async(
                args=[unit_creation.next_creation.id],
                countdown=unit_creation.next_creation.unit.creation_time,
                )
    except ObjectDoesNotExist:
        pass
    unit_creation.delete()

@task
def achieve_research(research_id):
    from models import TechnologyResearch
    research = TechnologyResearch.objects.get(id=research_id)
    research.tribe.increase_tech_level(research.technology)
    try:
        #TODO change that for an addition
        research.next_research.date_begin = timezone.now()
        research.next_research.save()
        achieve_research.apply_async(
                args=[research.next_research.id],
                countdown=research\
                        .next_research\
                        .technology\
                        .get_research_duration(research.level)
                )
    except TechnologyResearch.DoesNotExist:
        # if research.next_research does not exist
        pass
    research.delete()

@task
def achieve_construction(self):
    self.village.increase_building_level(self.building)
    try:
        self.next_construction.date_begin = timezone.now()
        self.next_construction.save()
        achieve_construction.apply_async(
                args=[self.next_research.id],
                countdown=self.building.get_construction_duration(
                                                self.building,
                                                self.level,
                                                )
                )
    except ObjectDoesNotExist:
        pass
    self.delete()

@task
def progress(mission_id):
    """
    Decides what to do next in a mission context
    """
    from models import Mission
    mission = Mission.objects.get(id=mission_id)
    new_position = mission.get_next_tile()
    eta = mission.compute_date_next_move()
    if new_position is None:
        if mission.routeelement_set.count() == 1:
            res = achieve_mission.apply_async(
                    args=[mission_id],
                    eta=eta,
                    )
        else:
            res = achieve_mission.apply_async(
                    args=[mission_id],
                    #TODO improve get_date_next_move to handle this case
                    eta=eta,
                    )
    else:
        try:
            mission.group.move(new_position)
        except mission.group.CannotMove:
            mission.group.log_report(type=11,
                    subject='Impossible de progresser',
                    body='Votre groupe ne peut poursuivre son chemin.'
                        ' Si vous pensez que ceci est une erreur, merci'
                        ' de nous le signaler'
                        )
            return mission.achieve_mission_move()
        res = progress.apply_async(
                args=[mission_id],
                eta=eta,
                )
    mission.date_next_move = eta
    mission.task_id = res.id
    mission.save()

@task
def achieve_mission(mission_id):
    """
    This method is called once the group is at destination.
    """
    from models import Mission
    mission = Mission.objects.get(id=mission_id)
    return getattr(mission,
                'achieve_mission_{}'.format(mission.mission_type),
                #let it commented for debug purpose
                #self.achieve_mission_stay
                )()
