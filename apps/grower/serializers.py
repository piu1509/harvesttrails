from rest_framework import serializers

from .models import Consultant, Grower



class GrowerSerializer(serializers.ModelSerializer):
    """Serializer for the grower object"""

    class Meta:
        model = Grower
        fields = "__all__"


class GrowerListSerializer(serializers.ModelSerializer):
    """Serializer for the grower object"""

    class Meta:
        model = Grower
        fields = ('id', 'name',)


class ConsultantListSerializer(serializers.ModelSerializer):
    """Serializer for the consultant object"""

    class Meta:
        model = Consultant
        fields = ('id', 'name',)


class ConsultantSerializer(serializers.ModelSerializer):
    """Serializer for the consultant object"""

    class Meta:
        model = Consultant
        fields = "__all__"


# class GrowerNotificationSerializer(serializers.ModelSerializer):
#     """Serializer for the GrowerNotification object"""

#     class Meta:
#         model = GrowerNotification
#         fields = "__all__"
