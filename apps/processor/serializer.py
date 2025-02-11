from rest_framework import serializers
from apps.processor.models import GrowerShipment



class GrowerShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrowerShipment
        fields = '__all__'