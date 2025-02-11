from rest_framework import serializers

from apps.farms import models


class FarmSerializer(serializers.ModelSerializer):
    """Serializes a Farm object"""
    class Meta:
        model = models.Farm
        fields = "__all__"


class FarmListSerializer(serializers.ModelSerializer):
    """Serializer to list farm along with area"""
    field_count = serializers.IntegerField()
    total_area = serializers.IntegerField()

    class Meta:
        model = models.Farm
        fields = ('id', 'name', 'field_count', 'total_area')


class FarmDetailSerializer(serializers.ModelSerializer):
    """Serializer class for farm detail view"""

    class Meta:
        model = models.Farm
        fields = "__all__"

class FarmJsonList(serializers.ModelSerializer):
    """Serializer to list farm along with area"""
    grower_name = serializers.ReadOnlyField(source='grower.name')
    class Meta:
        model = models.Farm
        fields = '__all__'
        # ('id', 'name','grower_name')