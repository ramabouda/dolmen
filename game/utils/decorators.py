#!/usr/bin/env python
#!vim: set fileencoding=utf-8 :


def resource_update_required(village):
    """
    Appelle la fonction Village.resource_update
    avant de s’executer. À utiliser avant une récolte
    ou un combat par exemple, pour vérifier si des
    membres du group sont morts de la famine.
    """
    def village_resource_update(func):
        village.resources_update()
        return func
    return village_resource_update

def income_update_required(village):
    """
    Calls the Village.income_update function.
    Use it after deathes, birthes, or gathering operations
    """
    def village_income_update(func):
        village.update_income()
        return func
    return village_income_update

def next_starvation_update(village):
    """
    update the date of the date of the next starvation.
    Needs to be called whenever the resources stop varying
    linearly (work indirectedly done by income_update_required)
    """
    def result(func):
        village.plan_next_starvation()
        return func
    return result
