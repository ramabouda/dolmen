#!vim: set fileencoding=utf-8 :
from re import compile
from models import Carte, Village, Tribe

APPLYING_URLS = [compile(r'^/game.*')]

class PopulateSessionMiddleware:
    """Middleware assuming that the user is logged in as
    it applies only to urls starting by "game" where login is
    forced by LoginRequiredMiddleware.

    It stores is session default tribe and village for the
    current user.
    """
    def process_request(self, request):
        path = request.path_info
        if any(m.match(path) for m in APPLYING_URLS):
            assert hasattr(request, 'user'), "The Populate Session middleware\
            is supposed to be used together with the LoginRequiredMiddleware\
            and hence supposes that a user is logged in when it applies"
            if 'map' not in request.session:
                #TODO handle many cartes case
                request.session['map'] = Carte.objects.all()[0]
            if 'tribe' not in request.session:
                #TODO handle many tribes case
                try:
                    request.session['tribe'] = request.user.tribe_set.all()[0]
                    request.session['village'] = Village\
                            .objects\
                            .filter(tribe=request.session['tribe'])\
                            .order_by('date_creation')[0]
                except IndexError:
                    last_id = Tribe.objects.order_by('id').last().id + 1
                    carte = Carte.objects.all()[0]
                    tribe = Tribe.create_tribe('New Tribe {}'.format(last_id), request.user, carte)
                    request.session['tribe'] = tribe

            if 'village' not in request.session:
                #get the first village by creation order. Can raise an exception
                # if there is no village for the tribe — which is theorically
                # impossible in the game context
                request.session['village'] = Village\
                        .objects\
                        .filter(tribe=request.session['tribe']).first()
        return None
