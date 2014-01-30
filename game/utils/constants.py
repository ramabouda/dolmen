#!vim: set fileencoding=utf-8 :
from django.conf import settings

INIT_TRIBE_RESOURCES = {
    'wood': 100,
    'food': 300,
    'silex': 100,
    'skin': 100,
    }

INIT_TRIBE_UNITS = {'warrior': 5, 'woman': 3}

STARVATION_LIMIT = 0

NB_VILLAGES_PER_TILE = 6

RANGED_UNITS = ['prowler', 'hunter']

GROUND_CHOICES = (
        (0, 'plain'),
        (1, 'forest'),
        (2, 'mountain'),
        (3, 'lake'),
        )

GROUND_PRODUCTIONS = {
        0: 1000,
        1: 1000,
        2: 1000,
        3: 1000,
        }

if settings.FAST_MOVES:
    MEAN_DELAYS = {
        'enter': 1,
        'internal_move': 1,
        'cross': 1,
        }
else:
    MEAN_DELAYS = {
        'enter': 1200,
        'internal_move': 600,
        'cross': 1800,
        }

VILLAGE_CREATION_NEEDED_RESOURCES = {
        'food': 200,
        'wood': 200,
        'skin': 200,
        'silex': 200,
        }
