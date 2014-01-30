#vim: set fileencoding=utf- :

from annoying.functions import get_object_or_None
from celery.task.control import revoke
from django.db import models
from technology import TechnologyKnowledge
from game import tasks



class UnitCreation(models.Model):
    """
    Represents the unit creations, storing the village that initiated that
    and managing the order of the creations.

    Provides a add_unit_creation(self, unittype, village, number) methods
    that helps inserting new creations
    """
    unit = models.ForeignKey('Human')
    village = models.ForeignKey('Village', editable=False)
    previous = models.OneToOneField(
            'UnitCreation',
            null=True, blank=True,
            related_name='next_creation',
            editable=False,
            on_delete=models.SET_NULL,
            )
    date_begin = models.DateTimeField(null=True, blank=True, editable=False)
    task_id = models.CharField(max_length=64, null=True, editable=False)

    class Meta:
        app_label = 'game'

    def time_length(self):
        return 0

    def delete(self):
        if self.task_id:
            revoke(self.task_id)
        return super(UnitCreation, self).delete()

    @staticmethod
    def add_unit_creation(unittype, village, number=1):
        """
        Add unit creations to the fifo creating list of the
        :model:`tribe.Village`.

        """
        last_unit_creation = get_object_or_None(
                UnitCreation,
                village=village,
                next_creation=None,
                )
        for i in xrange(number):
            if i > 0 or last_unit_creation is not None:
                #TODO check if the tribe has the required technologies
                last_unit_creation = UnitCreation.objects.create(
                        village=village,
                        unit=unittype,
                        previous=last_unit_creation,
                        )
            else:
                last_unit_creation = UnitCreation.objects.create(
                        village=village,
                        unit=unittype,
                        )
                tasks.achieve_enroll.apply_async(
                        args=[last_unit_creation.id],
                        countdown=last_unit_creation.unit.creation_time,
                        )


class TechnologyResearch(models.Model):
    """
    This model symbolizes the research of a tribe.Technology.
    It contains the tribe.Tribe object that performs the research,
    the tribe.Technology object that is to be searched, and
    optionnaly a link to another tibe.TechnologyResearch that
    is supposed to be performed before begining the new research.

    It also provides a add_techno_research method that automatically
    appends the new research to the end of the buffer.
    """
    tribe = models.ForeignKey('Tribe')
    technology = models.ForeignKey('Technology')
    previous = models.OneToOneField(
            'TechnologyResearch',
            null=True, blank=True,
            related_name='next_research'
            )
    level = models.PositiveSmallIntegerField(default=1)
    date_begin = models.DateTimeField(null=True, blank=True)
    task_id = models.CharField(max_length=64, blank=True, null=True, editable=False)

    class Meta:
        app_label = 'game'
        get_latest_by = 'date_begin'

    def time_length(self):
        return 0
    
    def delete(self):
        if self.task_id:
            revoke(self.task_id)
        return super(TechnologyResearch, self).delete()

    @staticmethod
    def add_techno_research(techno, tribe):
        """
        Add a research to the fifo researching list
        """
        last_techno_research = get_object_or_None(
                TechnologyResearch,
                tribe=tribe,
                next_research=None,
                )
        if last_techno_research is not None:
            try:
                TechnologyResearch.objects.create(
                        tribe=tribe,
                        technology=techno,
                        previous=last_techno_research,
                        level = tribe.technologyknowledge_set.get(technology=techno).level + 1,
                        )
            except TechnologyKnowledge.DoesNotExist:
                TechnologyResearch.objects.create(
                        tribe=tribe,
                        technology=techno,
                        previous=last_techno_research,
                        )
        else:
            try:
                a = TechnologyResearch.objects.create(
                        tribe=tribe,
                        technology=techno,
                        level = tribe.technologyknowledge_set\
                                .get(technology=techno).level + 1,
                        )
            except TechnologyKnowledge.DoesNotExist:
                a = TechnologyResearch.objects.create(
                        tribe=tribe,
                        technology=techno,
                        )
            tasks.achieve_research.apply_async(
                    args=[a.id],
                    countdown=a.technology.get_research_duration(
                                                    a.level,
                                                    )
                    )


class BuildingConstruction(models.Model):
    """
    This model symbolizes the construction of a tribe.Building.
    It contains the tribe.Village object that performs the construction,
    the tribe.Building object that is to be searched, and
    optionnaly a link to another tribe.BuildingConstruction that
    is supposed to be performed before begining the new construction.

    It also provides a add_building_construction method that automatically
    appends the new research to the end of the buffer.
    """
    village = models.ForeignKey('Village')
    building = models.ForeignKey('Building')
    level = models.PositiveSmallIntegerField(default=1)
    previous = models.ForeignKey(
            'BuildingConstruction',
            null=True, blank=True,
            related_name='next_construction'
            )
    date_begin = models.DateTimeField(null=True, blank=True)
    task_id = models.CharField(max_length=64, blank=True, null=True, editable=False)

    def delete(self):
        if self.task_id:
            revoke(self.task_id)
        return super(BuildingConstruction, self).delete()

    class Meta:
        app_label = 'game'

    def time_length(self):
        return 0

    @staticmethod
    def add_building_construction(building, village):
        """
        Add a construction to the fifo construction list
        """
        last_building_construction = get_object_or_None(
                BuildingConstruction,
                village=village,
                next_consruction=None,
                )
        if last_building_construction is not None:
            BuildingConstruction.objects.create(
                    village=village,
                    building=building,
                    previous=last_building_construction,
                    )
        else:
            a = BuildingConstruction.objects.create(
                    village=village,
                    building=building,
                    )
            tasks.achieve_construction.apply_async(
                    args=[a.id],
                    countdown=a.building.get_construction_duration(
                                                    a.building,
                                                    a.level,
                                                    )
                    )

