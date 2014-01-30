from django.contrib.admin import site
from django.contrib import admin
from models.alliances import *
from models.building import *
from models.group import *
from models.maps import *
from models.mission import *
from models.report import *
from models.resources import *
from models.technology import *
from models.tribe import *
from models.unit import *
from models.village import *
from models.virtuals import *
from models.messages import *
from forms.admin_forms import AdminCreateVillageForm, AdminCreateTribeForm, AdminCreateMapForm



class ShownStacks(admin.TabularInline):
    model = UnitStack
    extra = 3


class GroupAdmin(admin.ModelAdmin):
    inlines = [ShownStacks]
    list_display = ('__unicode__', 'position')


class HerdAdmin(admin.ModelAdmin):
    inlines = [ShownStacks]


class TypeHumanAdmin(admin.ModelAdmin):
    list_display = ('name', 'attack', 'defense', 'speed')
    fields = (('name', 'identifier'),
            ('attack', 'defense'),
            ('speed', 'consumption'),
            'cost',
            'creation_time',
            )
    list_editable = ('attack', 'defense', 'speed')


class ShownTiles(admin.TabularInline):
    model = Tile
    extra = 0


class InlineVillages(admin.TabularInline):
    model = Village
    extra = 1
    raw_id_fields = ('position',)


class CarteAdmin(admin.ModelAdmin):
    add_form = AdminCreateMapForm
    list_display = ('name', 'get_radius', 'cases_number')
    inlines = [ShownTiles]

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                })
        defaults.update(kwargs)
        return super(CarteAdmin, self).get_form(request, obj, **defaults)


class AllianceAdmin(admin.ModelAdmin):
    list_display = ('name', 'abreviation')
    readonly_fields = ('name', 'abreviation')


class GatheringAdmin(admin.ModelAdmin):
    list_display = ('group', 'resource', 'efficiency', 'production', 'date_update')


class MissionAdmin(admin.ModelAdmin):
    list_display = ('group', 'mission_type', 'get_target', 'date_begin', 'date_next_move')
    date_hierarchy = 'date_begin'
    radio_fields = {'mission_type': admin.HORIZONTAL}


class TribeAdmin(admin.ModelAdmin):
    add_form = AdminCreateTribeForm
    list_display = ('name', 'leader', 'date_creation')
    inlines = [InlineVillages]
    date_hierarchy = 'date_creation'
    search_fields = ('name', 'leader__username')
    readonly_fields = ('date_creation',)

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                })
        defaults.update(kwargs)
        return super(TribeAdmin, self).get_form(request, obj, **defaults)


class VillageAdmin(admin.ModelAdmin):
    add_form = AdminCreateVillageForm
    list_display = ('name', 'tribe', 'position', 'date_creation')
    date_hierarchy = 'date_creation'
    search_fields = ('name', 'tribe__name')
    readonly_fields = ('date_creation',)

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults.update({
                'form': self.add_form,
                })
        defaults.update(kwargs)
        return super(VillageAdmin, self).get_form(request, obj, **defaults)


class TechnologyKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('technology', 'tribe', 'level')
    search_fields = ('technology', 'tribe')
    list_editable = ('level',)

class RequirementAdmin(admin.ModelAdmin):
    list_display = ('target', 'need', 'level_required')
    list_editable = ('level_required',)

site.register(Alliance, AllianceAdmin)
site.register(Animal)
site.register(Building)
site.register(Carte, CarteAdmin)
site.register(ConstructedBuilding)
site.register(Cost)
site.register(Gathering, GatheringAdmin)
site.register(Group, GroupAdmin)
site.register(Human, TypeHumanAdmin)
site.register(Herd, HerdAdmin)
site.register(Mission, MissionAdmin)
site.register(Report)
site.register(Requirement, RequirementAdmin)
site.register(Resources)
site.register(Technology)
site.register(TechnologyKnowledge, TechnologyKnowledgeAdmin)
site.register(TechnologyResearch)
site.register(Tribe, TribeAdmin)
site.register(Village, VillageAdmin)
site.register(UnitCreation)
site.register(UnitRequirement, RequirementAdmin)
site.register(UnitStack)
site.register(RouteElement)
site.register(Message)
site.register(Thread)
