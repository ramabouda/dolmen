#!vim: set fileencoding=utf-8 :


from ..forms.add_progress import EnrollForm, TechnoResearchForm, BuildingConstructForm
from ..models import Tribe, Village, Carte, Tile, Technology, TechnologyKnowledge, ConstructedBuilding, Building, Human
from ..utils.exceptions import CannotPay, TechnologyNeeded
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.generic import FormView, ListView
from extra_views import FormSetView

def main_view(request, tribe_id=None):
    """
    Main view for the game. Displays the informations for
    one tribe and the main village of this tribe.
    """
    if tribe_id is not None:
        tribe = get_object_or_None(Tribe, id=tribe_id)
        if tribe is not None and tribe.leader == request.user:
            request.session['tribe'] = tribe
            if 'village' in request.session:
                del request.session['village']
        return redirect(reverse_lazy('game:main_view'))

    return render_to_response(
            "game/game.html",
            context_instance=RequestContext(request),
            )


@render_to('game/map.html')
def view_map(request, map_id=None):
    """Testing view"""
    if map_id is not None and map_id <> '':
        request.session['map'] = Carte.objects.get(id=map_id)
    else:
        if 'map' not in request.session:
            request.session['map'] = Carte.objects.all()[0]
    if 'tribe' in request.session:
        tribe = request.session['tribe']
    else:
        tribe = request.user.tribe_set.all()[0]
    carte = request.session['map']
    tiles = tribe.dispatch_tiles()
    # TODO
    center = Tile.objects.filter(carte=carte).filter(x=5).get(y=5)
    return {
                'tiles': tiles,
                'center': center,
            }


class EnrollView(FormSetView):
    """
    View that manages the enrollment of new units.

    **Context**

        ``formset``
            The formset used to gather the infomation

    **Template**

    :template:`game/enroll.html`
    """
    form_class = EnrollForm
    template_name = 'game/enroll.html'

    def post(self, request, *args, **kwargs):
        if 'village' not in self.request.session:
            messages.error(
                    self.request,
                    'merci de sélectionner un village avant de continuer',
                    )
            return HttpResponseRedirect('/game')
        else:
            village = Village.objects.get(id=self.request.session['village'].id)
        formset = self.construct_formset()
        for form in formset:
            try:
                if form.is_valid():
                    village.add_unit_creation(
                            form.cleaned_data['unit_type'],
                            form.cleaned_data['number'],
                            )
                    messages.success(
                            self.request,
                            'le recrutement a été initialisé',
                            )
            except CannotPay:
                messages.error(
                        self.request,
                        "Vous n'avez pas les moyens de recruter tous ces soldats."
                        "Le recrutement de ceux que vous pouvez nourrir a commencé",
                        )
            except TechnologyNeeded as e:
                messages.error(
                        self.request,
                        "You need to research this technology first: {}"\
                                .format(Technology.objects.get(id=e.value)),
                        )
        return HttpResponseRedirect('/game/enroll')


    def get_context_data(self, **kwargs):
        context = super(EnrollView, self).get_context_data(**kwargs)
        context['available_units'] = Human.objects.all()
        return context

    def dispatch(self, *args, **kwargs):
        return super(EnrollView, self).dispatch(*args, **kwargs)


class TechnologyResearchView(FormView):
    """
    View that displays the known :model:`game.Technology`s and provides
    links to learn new technologies

    **Context**

        ``form``
            Form provided to launch a new techno reasearch

        ``available_technos``
            QuerySet that contains the technos for which the
            current tribe has all the necessary requirements

        ``need_requirement_upgrade``
            A set of ID’s of the technologies whose required
            technologies are not to a higher level

    **Template**

    :template:`game/research_techno.html`

    """
    form_class = TechnoResearchForm
    success_url = '/game/research_techno/'
    template_name = 'game/research_techno.html'

    def dispatch(self, *args, **kwargs):
        return super(FormView, self).dispatch(*args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(TechnologyResearchView, self).get_context_data(**kwargs)
        a, b = self.request.session['tribe'].get_reachable_technos()
        context['available_technos'] = a
        context['need_requirement_upgrade'] = b
        
        tribe = self.request.session['tribe']
               
        #techno -> {
            #form:form,
            #techno_knowledge:tk,
            #required:{
            #    need:techno_need,
            #    level_required:int,
            #    actual_level:int}
            #    }
            #}
        context['technos'] = {
            techno: {
                'form':self.form_class(initial={'technology':techno.pk}),
                'techno_knowledge':None,
                'required':{need :
                    {'level_required':need.level_required,\
                    'actual_level':tribe.get_techno_level_by_name(need.need.identifier)} \
                    for need in techno.need.all()}} \
            for techno in Technology.objects.all()
            }
        for techno,infos in context['technos'].items():
            try:
                tk = tribe.technologyknowledge_set.get(technology=techno)
                context['technos'][techno]['techno_knowledge'] = tk
                for need in infos['required']:
                    context['technos'][techno]['required'][need]['level_required'] += tk.level
            except TechnologyKnowledge.DoesNotExist:
                pass
            
        return context


    def form_valid(self, form):
        try:
            village = Village.objects.get(id=self.request.session['village'].id)
            village.research_techno(
                    Technology.objects.get(pk=form.cleaned_data['technology'])
                    )
            messages.success(self.request,
                    'Your research has been successfully initiated'
                    )
        except CannotPay:
            messages.error(
                    self.request,
                    "You don't have enough resources to pay this research"
                    )
        except TechnologyNeeded as e:
            messages.error(
                    self.request,
                    "You need to research this technology first: {}"\
                            .format(Technology.objects.get(id=e.value)),
                    )
        except Technology.DoesNotExist as e:
            messages.error(
                    self.request,
                    "This technology does not exists",
                    )
        except Exception as e:
            messages.error(
                    self.request,
                    "Error: This technology can't be researched.",
                    )
        return super(FormView, self).form_valid(form)

    def form_invalid(self, form):
        return super(FormView, self).form_invalid(form)


class BuildingView(FormView):
    """
    View that displays the known :model:`village.Building`s and provides
    links to build new buildings

    **Context**


        ``available_technos``
            QuerySet that contains the technos for which the
            current tribe has all the necessary requirements

        ``need_requirement_upgrade``
            A set of ID’s of the technologies whose required
            technologies are not to a higher level

    **Template**

    :template:`tribe/build.html`

    """
    form_class = BuildingConstructForm
    success_url = '/game/build/'
    template_name = 'game/build.html'

    def dispatch(self, *args, **kwargs):
        return super(FormView, self).dispatch(*args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(BuildingView, self).get_context_data(**kwargs)
        a, b = self.request.session['tribe'].get_reachable_technos()
        
        village = self.request.session['village']
                
        #building -> {
            #form:the_form,
            #level:the_level
            #building:the_building
            #building_constructed:ConstructedBuilding
            #}
            
            
        context['buildings'] = [
            {
                'form':self.form_class(initial={'building':building.pk}),
                'building':building,
                'building_constructed': get_object_or_None(ConstructedBuilding, building=building, village=village),
                'cost_next_upgrade': village.building_cost_next_level(building),
                'can_pay': village.can_pay(village.building_cost_next_level(building))
            } \
            for building in Building.objects.all()
            ]
        
        return context


    def form_valid(self, form):
        try:
            village = Village.objects.get(id=self.request.session['village'].id)
            village.research_techno(
                    Technology.objects.get(pk=form.cleaned_data['technology'])
                    )
            messages.success(self.request,
                    'Your research has been successfully initiated'
                    )
        except CannotPay:
            messages.error(
                    self.request,
                    "You don't have enough resources to pay this research"
                    )
        except TechnologyNeeded as e:
            messages.error(
                    self.request,
                    "You need to research this technology first: %s" % e.value,
                    )
        except Technology.DoesNotExist as e:
            messages.error(
                    self.request,
                    "This technology does not exists",
                    )
        return super(FormView, self).form_valid(form)

    def form_invalid(self, form):
        return super(FormView, self).form_invalid(form)


class MailBoxView(ListView):
    """
    Display the list of available :model:`game.Threads` for the current
    :model:`game.Tribe`.

    **Context**

        ``threads``

    **Template**

    :template:`game/mailbox.html`
    """
    context_object_name = 'threads'
    template_name = 'game/mailbox.html'

    def get_queryset(self):
        tribe = self.request.session['tribe']
        return tribe.received_thread.all()

    def dispatch(self, *args, **kwargs):
        if 'tribe' not in self.request.session:
            return HttpResponseRedirect(reverse_lazy('game:choose_tribe'))
        return super(MailBoxView, self).dispatch(*args, **kwargs)


class ReportsView(ListView):
    """
    Display the list of available :model:`game.Threads` for the current
    :model:`game.Tribe`.

    **Context**

        ``reports``

    **Template**

    :template:`game/reports_list.html`
    """
    context_object_name = 'reports'
    template_name = 'game/reports_list.html'

    def get_queryset(self):
        tribe = self.request.session['tribe']
        return tribe.report_set.all()

    def dispatch(self, *args, **kwargs):
        if 'tribe' not in self.request.session:
            return HttpResponseRedirect(reverse_lazy('game:choose_tribe'))
        return super(ReportsView, self).dispatch(*args, **kwargs)
