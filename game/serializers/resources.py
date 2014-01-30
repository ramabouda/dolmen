#vim: set fileencoding=utf-8 :

from ..models import Resources
from rest_framework import serializers

class ResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resources
