#vim: set fileencoding=utf-8 :

from ..models import Mission, Group
from ..models.mission import MISSION_CHOICES
from group import StackSerializer
from rest_framework import serializers

class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ('group', 'mission_type', 'date_begin',
                'date_next_move', 'target_id', 'route')
        read_only_fields = fields

class IntegerListField(serializers.WritableField):
    def from_native(self, data):
        return data
    
    def to_native(self, data):
        return data

class MissionRequestSerializer(serializers.Serializer):
    """Receive mission request. It needs to be passed the request context!"""
    split_group = StackSerializer(many=True, required=False)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    mission_type = serializers.ChoiceField(choices=MISSION_CHOICES)
    target_id = serializers.IntegerField()
    route = IntegerListField()

    def validate_group(self, attrs, source):
        "Check that the group belongs to the user"
        group = attrs[source]
        if not group.get_tribe() == self.context['request'].session['tribe']:
            raise serializers.ValidationError(
                    "Trying to send a group of another tribe")
        return attrs

    def validate_split_group(self, attrs, source):
        if source not in attrs:
            return attrs
        split_group = attrs[source]
        origin_group = Group.objects.get(id=attrs['group'])
        split_dict = {int(k): int(split_group[k]) for k in split_group}
        if not origin_group.can_split(split_dict):
            raise serializers.ValidationError(
                    "Cannot split this way")
        else:
            return attrs
    
    #def restore_object(self, attrs, instance=None):
        #"""set a my_dict attribute and return the parent function"""
        #self.my_dict = attrs.copy()
        #return super(MissionRequestSerializer, self)\
                #.restore_object(attrs, instance)
