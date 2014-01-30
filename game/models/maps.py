#vim: set fileencoding=utf-8 :


from django.db import models
from django.db.models import Count, Sum, Max
from django.template.loader import render_to_string
from game.utils.constants import NB_VILLAGES_PER_TILE, GROUND_CHOICES, GROUND_PRODUCTIONS
from resources import Gathering
import math
import random



class Tile(models.Model):
    """
    Represent a tile of the map.

    Basically a tile is a position, and a ground type.
    The class provides methods to compute distances to
    other tiles as well as control methods about resources
    gathering or village building.
    """
    ground = models.PositiveSmallIntegerField(choices=GROUND_CHOICES, default=0)
    x = models.SmallIntegerField()
    y = models.SmallIntegerField()
    z = models.SmallIntegerField()
    carte = models.ForeignKey('Carte')
    # Une rivière est définie par une relation entre deux cases voisines
    #river = models.ManyToManyField('Tile', null=True, blank=True)

    class Meta:
        app_label = 'game'

    def __unicode__(self):
        """
        >>> tile = Tile(x=1, y=1, z=1, carte=Carte(name='foo'))
        >>> print tile.__unicode__()
        1 1 1 dans carte foo
        """
        return '%s %s %s dans carte %s'\
                % (
                        str(self.x),
                        str(self.y),
                        str(self.z),
                        self.carte
                        )

    def ortho_x(self):
        """ X position in an orthogonal system """
        return 0

    def ortho_y(self):
        """ Y position in an orthogonal system """
        return 0

    def ortho_coords(self):
        """ a string with the position in the orthogonal system """
        return '[%s:%s]' % (self.ortho_x(), self.ortho_y())

    def distance(self, autre_case):
        """
        Calcule la distance entre deux cases. Si les deux cases sont
        sur des cartes différentes, renvoie None.

        >>> carte1 = Carte(id=100000)
        >>> carte2 = Carte(id=100001)
        >>> case1 = Tile(x=1,y=1,z=1, carte=carte1)
        >>> case2 = Tile(x=2, y=1, z=1, carte=carte1)
        >>> case1.distance(case2)
        1
        >>> case2 = Tile(x=2, y=1, z=1, carte=carte2)
        >>> case1.distance(case2) == None
        True
        """
        if not self.carte_id == autre_case.carte_id:
            return None
        return max(
                abs(self.x - autre_case.x),
                abs(self.y - autre_case.y),
                abs(self.z - autre_case.z)
                )

    def can_add_village(self):
        """
        true if the tile is not overcrowded
        """
        return self.village_set.count() < NB_VILLAGES_PER_TILE

    def naive_path_finding(self, destination):
        """
        Calcule le chemin le plus court géographiquement
        parlant : donne une trajectoire à vol d’oiseau, sans
        prendre en compte les rivières ni rien d’autre.

        >>> carte = Carte()
        >>> carte.save()
        >>> case1 = (Tile(x=1, y=1, z=-2))
        >>> case2 = (Tile(x=2, y=2, z=-4))
        >>> case3 = (Tile(x=1, y=2, z=-3))
        >>> carte.tile_set.add(case1, case2, case3)
        >>> case1.save()
        >>> case2.save()
        >>> case3.save()
        >>> case1.naive_path_finding(case2) == [case1, case3, case2]
        True

        >>> carte1 = Carte()
        >>> carte1.save()
        >>> carte1.tile_set.add(case2)
        >>> case1.naive_path_finding(case2) == None
        True
        """
        if self.carte != destination.carte:
            return None
        (x_dest, y_dest, z_dest) = (destination.x, destination.y, destination.z)
        (x_temp, y_temp, z_temp) = (self.x, self.y, self.z)
        temp = []
        while (x_temp, y_temp, z_temp) != (x_dest, y_dest, z_dest):
            temp += [(x_temp, y_temp, z_temp)]
            i = min(
                    abs(x_dest - x_temp),
                    abs(y_dest - y_temp),
                    abs(z_dest - z_temp)
                    )
            if abs(x_dest - x_temp) == i:
                y_temp -= cmp(y_temp, y_dest)
                z_temp -= cmp(z_temp, z_dest)
            elif abs(y_dest - y_temp) == i:
                x_temp -= cmp(x_temp, x_dest)
                z_temp -= cmp(z_temp, z_dest)
            else:
                x_temp -= cmp(x_temp, x_dest)
                y_temp -= cmp(y_temp, y_dest)
        temp += [(x_dest, y_dest, z_dest)]
        return [self.carte.tile_set.filter(x=xi).get(y=yi)
                for (xi, yi, zi) in temp]

    def get_production_per_head(self):
        """
        Return the production of the resource if one persone work with the
        maximal efficiency
        """
        #TODO
        return 50

    def get_max_production(self):
        """
        return the optimized revenues of the tile.
        """
        return GROUND_PRODUCTIONS[self.ground]

    def compute_gathering_production(self):
        """
        Compute the gathering production of all the gathering
        objects concerning the tile
        """
        gatherings = Gathering.objects\
                .filter(group__position=self)\
                .annotate(workers_number=Sum('group__unitstack__number'))
        total_workers_number = 0
        for gathering in gatherings:
            total_workers_number +=\
                    gathering.workers_number\
                    * gathering.efficiency
        total_production = min(
                self.get_max_production(),
                self.get_production_per_head() * total_workers_number,
                )
        for gathering in gatherings:
            gathering.production =\
                    gathering.workers_number\
                    * gathering.efficiency\
                    * total_production\
                    / total_workers_number
            gathering.save()
            gathering.village.resources_update()
            gathering.village.update_income()

    def get_details_html(self):
        """
        return an html string giving in an eye-candy view all the
        data corresponding to the tile
        """
        return render_to_string('game/tile_details.html', {'tile': self})

    def get_resource(self):
        match = {
                0: 'food',
                1: 'wood',
                2: 'silex',
                }
        return match[self.ground]

class Carte(models.Model):
    #TODO refactor to something else than map since map is a reserved word
    #in Python
    """
    A map is modelled as a set of tiles.
    """
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True)

    class Meta:
        app_label = 'game'

    @staticmethod
    def create_map(rayon=30, name='new_map'):
        """
        Creates a new map, cascading to creating
        the corresponding tiles according to
        `rayon` parameter.
        """
        new_carte = Carte(name=name, description='')
        new_carte.save()
        coef_grounds = len(GROUND_CHOICES) - 0.7
        for xc in range(2 * rayon + 1):
            for yc in range(2 * rayon + 1):
                if xc + yc >= rayon and xc + yc <= 3 * rayon:
                    ground = math.trunc(random.uniform(0, coef_grounds))
                    tile = Tile(x=xc,
                            y=yc,
                            z=xc + yc,
                            carte=new_carte,
                            ground=ground
                            )
                    tile.save()
        return new_carte

    def __unicode__(self):
        return self.name

    def get_radius(self):
        max_x = self.tile_set.all().aggregate(x__max=Max('x'))['x__max']
        if max_x:
            return max_x / 2
        else:
            return 0

    def cases_number(self):
        return self.tile_set.all().count()

    def get_disque_cases(self, centre, rayon):
        return self.tile_set\
                .filter(x__range=(centre.x - rayon, centre.x + rayon))\
                .filter(y__range=(centre.y - rayon, centre.y + rayon))\
                .filter(z__range=(centre.z - rayon, centre.z + rayon))

    def get_free_village_position(self, centre=None, rayon=None):
        """
        Renvoie une tile prise au hasard dans la carte concernée,
        dans une zone délimitée par les paramètres, qui peut héberger
        un village.
        param:
            centre:
                le centre de la zone
            rayon:
                le rayon de la zone de recherche
        return:
            un objet Tile
        """
        if centre == None or rayon == None:
            available_tiles = self.tile_set\
                    .annotate(num_villages=Count('village'))\
                    .filter(num_villages__lt=NB_VILLAGES_PER_TILE)\
                    .exclude(ground=3)\
                    .all()
        else:
            available_tiles = self.get_disque_cases(centre, rayon)\
                    .annotate(num_villages=Count('village'))\
                    .filter(num_villages__lt=NB_VILLAGES_PER_TILE)\
                    .exclude(ground=3)\
                    .all()
        return random.choice(available_tiles)

    @staticmethod
    def is_a_path(path):
        """
        Assert True if the path (as a list of tiles ids)
        is valid, ie if the tiles are
        adjacent and if there is no lake
        """
        tiles = list(Tile.objects.filter(id__in=path))
        tiles.sort(key=lambda tile: path.index(tile.id))
        x_prev = 0
        y_prev = 0
        z_prev = 0
        map_prev = 0
        init = True
        for tile in tiles:
            if tile.ground == GROUND_CHOICES[-1][0]:
                return False
            if not init:
                if abs(tile.x - x_prev) > 1\
                        or abs(tile.y - y_prev) > 1\
                        or abs(tile.z - z_prev) > 1\
                        or map_prev <> tile.carte:
                    return False
            else:
                init = False
            x_prev = tile.x
            y_prev = tile.y
            z_prev = tile.z
            map_prev = tile.carte
        return True
