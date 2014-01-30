from django import forms
from ..models import Technology, Human

class LaunchTechnoResearchForm(forms.Form):
    """Provide a form to launch a technology research"""
    technology = forms.ModelChoiceField(
            queryset = Technology.objects.all(),
            )


class TechnoResearchForm(forms.Form):
    """Provide a form to launch a technology research"""
    technology = forms.IntegerField(widget=forms.HiddenInput)

class BuildingConstructForm(forms.Form):
    """Provide a form to launch a building construction"""
    building = forms.IntegerField(widget=forms.HiddenInput)


class EnrollForm(forms.Form):
    unit_type = forms.ModelChoiceField(
            queryset=Human.objects.all(),
            empty_label=None,
            )
    number = forms.IntegerField()

