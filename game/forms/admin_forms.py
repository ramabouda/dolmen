from django import forms
from ..models.village import Village
from ..models.tribe import Tribe
from ..models.maps import Carte

class AdminCreateVillageForm(forms.ModelForm):
    """
    A forms that simplifies the creation of a new village.
    """
    class Meta:
        model = Village
        fields = ('name', 'tribe')

    def save(self, commit=True):
        #TODO set resources, inhabitants...
        village = super(AdminCreateVillageForm, self).save(commit=False)
        village = Village.create_village(
                self.cleaned_data['tribe'],
                self.cleaned_data['name'],
                )
        return village

class AdminCreateTribeForm(forms.ModelForm):
    """
    A forms that simplifies the creation of a new tribe.
    """
    class Meta:
        model = Tribe
        fields = ('name', 'leader')

    def save(self, commit=True):
        tribe = super(AdminCreateTribeForm, self).save(commit=False)
        tribe = Tribe.create_tribe(
                self.cleaned_data['name'],
                self.cleaned_data['leader'],
                #TODO
                Carte.objects.all()[0]
                )
        return tribe

class AdminCreateMapForm(forms.ModelForm):
    """
    A forms that simplifies the creation of a new map.
    """
    radius = forms.IntegerField()
    class Meta:
        model = Tribe

    def save(self, commit=True):
        carte = super(AdminCreateMapForm, self).save(commit=False)
        carte = Carte.create_map(
                self.cleaned_data['radius'],
                self.cleaned_data['name'],
                )
        carte.description = self.cleaned_data['description']
        return carte
