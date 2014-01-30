#vim: set fileencoding=utf-8 :

from ..models import Tile
from rest_framework import serializers

class TileRendererSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('ground', 'x', 'y', 'z')
        read_only_fields = fields
