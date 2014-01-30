#!/usr/bin/python
#vim: set fileencoding=utf-8 :
from django import template


register = template.Library()


@register.filter
def position_tile(tile, centre):
    """
    Calcule la position absolue d’une tile de la carte en connaissant la tile qui
    doit être au centre.

    Attention:
        utilise la largeur de la tile en hard-code, par praticité de développement.
        À changer !
    """
    largeur=62
    hauteur=71
    x_rel = tile.x - centre.x
    y_rel = tile.y - centre.y
    z_rel = tile.z - centre.z
    y = (x_rel+z_rel)*largeur/2+300
    x = y_rel*hauteur*3/4+300
    zindex = 1000 - int(y/10)
    #TODO fix the translation constant
    return 'left: {}px; bottom: {}px; z-index: {}'.format(x, y, zindex)
