#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from ..utils.combat import Combat
from ..models.group import Group, UnitStack
from django.forms.models import inlineformset_factory
from annoying.decorators import render_to
from django import forms


class SimulationParamForm(forms.Form):
    nb_simuls = forms.IntegerField(
        help_text='Laisser vide pour voir les détais d\'un combat'
        )


@render_to('game/tests/simulateur_combat.html')
def simulateur_combat(request):
    UniteFormSet = inlineformset_factory(Group, UnitStack, extra=5, max_num=5)
    groups = {}
    #attack
    groups[0] = Group(id=8000)
    #defense
    groups[1] = Group(id=8001)
    report = ''
    if request.method == 'POST':
        attack_formset = UniteFormSet(
                request.POST,
                request.FILES,
                prefix='attack',
                instance=groups[0]
                )

        defense_formset = UniteFormSet(
                request.POST,
                request.FILES,
                prefix='defense',
                instance=groups[1]
                )

        param = SimulationParamForm(
                request.POST,
                request.FILES,
                prefix='params'
                )

        if attack_formset.is_valid() and defense_formset.is_valid():
            attack = attack_formset.save()
            defense = defense_formset.save()
            for i in xrange(len(attack)):
                attack[i].id = 99 - i
            for i in xrange(len(defense)):
                defense[i].id = 100 + i

            if param.is_valid():
                nb_simulations = min(1000, param.cleaned_data['nb_simuls'])
                victoires = 0
                defaites = 0
                nuls = 0
                nb_rounds = 0
                nb_attaquants = 0
                nb_defenseurs = 0
                nb_attaquants_survivants = 0
                nb_defenseurs_survivants = 0

                for i in xrange(nb_simulations):
                    combat = Combat(groups[0], groups[1])
                    nb_attaquants += len(combat.units_attacker)
                    nb_defenseurs += len(combat.units_defender)
                    combat.fight()
                    nb_rounds += combat.current_round
                    nb_attaquants_survivants += len(combat.units_attacker)
                    nb_defenseurs_survivants += len(combat.units_defender)

                    if combat.is_attacker_winner() is None:
                        nuls += 1
                    elif combat.is_attacker_winner():
                        victoires += 1
                    else:
                        defaites += 1

                report = 'victoires : %s, \
                        défaites : %s, \
                        nuls : %s, \
                        durée moyenne : %s rounds, \
                        nb moyen d’attaquants à l’issue \
                            du dernier round : %s, \
                        nb moyen de défenseurs à l’issue du \
                            dernier round : %s, \
                        attaquants survivants : %s, \
                        defenseurs survivants : %s' \
                        % (
                                victoires,
                                defaites,
                                nuls,
                                nb_rounds / nb_simulations,
                                nb_attaquants / nb_simulations,
                                nb_defenseurs / nb_simulations,
                                nb_attaquants_survivants / nb_simulations,
                                nb_defenseurs_survivants / nb_simulations,
                                )
            else:
                combat = Combat(groups[0], groups[1])
                report = combat.report
            groups[0].delete()
            groups[1].delete()
    else:
        param = SimulationParamForm(prefix='param')
        attack_formset = UniteFormSet(prefix='attack', instance=groups[0])
        defense_formset = UniteFormSet(prefix='defense', instance=groups[1])
    return {
            'attack_formset': attack_formset,
            'defense_formset': defense_formset,
            'param_form': param,
            'report': report
            }
