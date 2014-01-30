#vim: set fileencoding=utf-8 :

from ..models import Report
from rest_framework import serializers
from rest_framework import permissions

class ReportPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tribe == request.session['tribe']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'type', 'village', 'date',
                'read', 'subject', 'body')
        read_only_fields = ('id', 'type', 'village',
                'date', 'subject', 'body')
