#!/usr/bin/python
# vim: set fileencoding=utf-8 :


from ..models import Tribe, Carte, Village, Group
from django.views.generic import FormView, ListView, View, RedirectView
from django.forms import ModelForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect



class NewTribeForm(ModelForm):
    """
    Form used by the NewTribe view
    """
    class Meta:
        model = Tribe
        fields = ('name', )


class NewTribe(FormView):
    """
    Vue gérant la création d'une nouvelle :model:`tribe.Tribe` à
    partir d'un formulaire avec uniquement
    le nom de la :model:`tribe.Tribe` à créer. Tout le reste est
    automatiquement affecté par la fonction
    :model:`tribe.Tribe`.create_tribe.

    **Context**

        ``form``
            formulaire de création de la nouvelle :model:`tribe.Tribe`

    **template**

    :template:`tribe/create_tribe.html`

    """

    form_class = NewTribeForm
    success_url = '/game'
    template_name = 'game/create_tribe.html'

    @method_decorator(\
            user_passes_test(\
            lambda u:\
                u.is_authenticated()\
                and (
                    u.has_perm('tribe.can_have_several_tribes')\
                            or u.tribe_set.count() == 0\
                            )
                )\
            )
    def dispatch(self, *args, **kwargs):
        return super(NewTribe, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        #TODO select the right map
        carte = Carte.objects.all()[0]

        self.request.session['tribe'] = Tribe.create_tribe(
                form.cleaned_data['name'],
                self.request.user,
                carte)
        return super(FormView, self).form_valid(form)

    def form_invalid(self, form):
        return super(FormView, self).form_invalid(form)


class ChooseTribe(ListView):
    """
    View that displays the tribes owned by the user, with links to allow him
    to choose the :model:`tribe.Tribe` he wants to connect to.

    **Context**

        ``tribes``
            the tribes owned by the user

    **Template**

    :template:`tribe/choose_tribe.html`

    """
    context_object_name = 'tribes'
    template_name = 'game/choose_tribe.html'

    def get_queryset(self):
        tribes = Tribe.objects.filter(leader=self.request.user)
        return tribes

    def dispatch(self, *args, **kwargs):
        if Tribe.objects.filter(leader=self.request.user).count() == 1:
            return redirect(
                    'game:choose_tribe_by_id',
                    Tribe.objects.get(leader=self.request.user).id,
                    )
        return super(ChooseTribe, self).dispatch(*args, **kwargs)


class ChooseVillage(View):
    """
    View used to set a new village in the session. Directly redirects
    to the main game page (TO BE CHANGED FOR THE PREVIOUS PAGE)
    """

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        village = Village.objects.get(id=self.args[0])
        if village.tribe == self.request.session['tribe']:
            self.request.session['village'] = village
            if request.is_ajax():
                return HttpResponse()
            else:
                return HttpResponseRedirect('/game')
        else:
            return HttpResponseForbidden()


class ChooseGroup(RedirectView):
    """
    View use to set a new group in the session. Redirects to the
    url passed in the 'next' get argument.
    """
    url = ''

    def dispatch(self, *args, **kwargs):
        return super(ChooseGroup, self).dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        group = Group.objects.get(id=self.args[0])
        if group.get_tribe() == self.request.session['tribe']:
            self.request.session['group'] = group
        return self.request.REQUEST['next']
