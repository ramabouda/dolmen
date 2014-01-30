#!/usr/bin/python
#vim: set fileencoding=utf-8 :
from django.forms import ModelForm
from game.models.orga import Group, Composition

class GroupeForm(ModelForm):
	class Meta:
		model = Group
		exclude = ('resources', 'position', 'village',)

class UnitStackForm(ModelForm):
	class Meta:
		model = Composition
		exclude = ('group',)


