#vim: set fileencoding=utf-8 :

from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from game.models import Carte, Mission, Group, Tile, Report, Resources, Village


@dajaxice_register
def mission_request(
        request,
        group_id,
        path,
        mission_type='move',
        target_id=None,
        split_group=None,
        resources=None,
        ):
    path = simplejson.loads(path)
    origin_group = Group.objects.get(id=group_id)

    if split_group:
        split_group = simplejson.loads(split_group)
        split_dict = {int(k): int(split_group[k]) for k in split_group}
        try:
            group = origin_group.split(split_dict) or origin_group
        except origin_group.CannotSplit:
            return simplejson.dumps(
                    {'message':
                        'You cannot split this way'
                    }
                )
    else:
        group = origin_group

    if resources:
        resources = Resources.dict_to_resources(simplejson.loads(resources))
        if resources:
            try:
                group.take_resources(origin_group.inhabitants_of, resources)
            except Village.DoesNotExist:
                pass
            if split_group:
                group.take_resources(origin_group, resources)

    if group.position_id == path[0]\
            and group.get_tribe() == request.session['tribe']\
            and Carte.is_a_path(path):
                #try:
        Mission.start_mission(
                    group,
                    path,
                    mission_type,
                    target_id,
                    )
        #TODO more precise handling of exceptions
        return simplejson.dumps(
                {
                    'message': 'le groupe part en expedition'
                }
                )
    return simplejson.dumps({'message':'id du groupe:' + str(group_id)})

@dajaxice_register
def tile_details_request(request, tile_id):
    tribe = request.session['tribe']
    tile = Tile.objects.get(id=tile_id)
    if tile in tribe.get_seen_cases():
        html = tile.get_details_html()
        return simplejson.dumps({'html':html})
    return simplejson.dumps({'alert':'case non vue'})

@dajaxice_register
def delete_report(request, report_id):
    tribe = request.session['tribe']
    report = Report.objects.get(id=report_id)
    if report.tribe == tribe:
        report.delete()
        return simplejson.dumps({'success':True})
    return simplejson.dumps({'message':'message non trouvé'})

@dajaxice_register
def mark_read_report(request, report_id):
    tribe = request.session['tribe']
    report = Report.objects.get(id=report_id)
    if report.tribe == tribe:
        report.read = True
        report.save()
        return simplejson.dumps({'success':True})
    return simplejson.dumps({'message':'message non trouvé'})

@dajaxice_register
def mark_unread_report(request, report_id):
    tribe = request.session['tribe']
    report = Report.objects.get(id=report_id)
    if report.tribe == tribe:
        report.read = False
        report.save()
        return simplejson.dumps({'success':True})
    return simplejson.dumps({'message':'message non trouvé'})

@dajaxice_register
def change_village_name(request, new_name):
    escaped_name = str(new_name).strip()
    if escaped_name:
        request.session['village'].name = new_name
        request.session['village'].save()

@dajaxice_register
def change_tribe_name(request, new_name):
    escaped_name = str(new_name).strip()
    if escaped_name:
        request.session['tribe'].name = new_name
        request.session['tribe'].save()
