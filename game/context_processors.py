#!/usr/bin/env python
#!vim: set fileencoding=utf-8 :

from models.village import Village
from models.tribe import Tribe


def add_common_template_data(request):
    """
    Template context processor that add to each request with a
    connected tribe and village, the data concerning the resources
    etc
    """
    if 'tribe' in request.session and 'village' in request.session:
        # need to do that to update the objects in session
        tribe = Tribe.objects.get(id=request.session['tribe'].id)
        village = Village.objects.select_related('tribe__name').get(id=request.session['village'].id)
        village.resources_update()  #  TODO fixit when the last resources_update was too long ago
        resources = village.resources
        village_income = village.income
        village_choices = Village.objects\
                .filter(tribe=tribe)\
                .exclude(id=village.id)
        village_groups = village.group_set.select_related('mission').prefetch_related('unitstack_set')
        tribe.divinity_update()
        fertility = village.fertility
        t = tribe.technologyresearch_set.order_by('date_begin')
        e = village.unitcreation_set.order_by('date_begin')

        result = {
                'tribe': tribe,
                'village': village,
                'resources': resources,
                'village_income': village_income,
                'village_choices': village_choices,
                'village_groups': village_groups,
                'fertility': fertility,
                }
        if t.exists():
            current_research = t[0]
            result['current_research'] = current_research

        if e.exists():
            current_enrollement = e[0]
            result['current_enrollement'] = current_enrollement

        return result

    else:
        return {}
