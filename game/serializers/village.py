#vim: set fileencoding=utf-8 :

from ..models import Village
from rest_framework import serializers
from resources import ResourcesSerializer

class VillageSerializer(serializers.ModelSerializer):
    resources = ResourcesSerializer(source='resources', many=False)
    income = ResourcesSerializer(source='income', many=False)
    class Meta:
        model = Village
        fields = ('name', 'resources',
                'fertility', 'tribe', 'position', 'income', 'group_set')
