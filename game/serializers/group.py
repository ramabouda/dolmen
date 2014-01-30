#vim: set fileencoding=utf-8 :

from ..models import Group, UnitStack
from rest_framework import serializers

class GroupSerializer(serializers.ModelSerializer):
    #TODO handle nested serializers with position
    class Meta:
        model = Group

class StackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitStack
