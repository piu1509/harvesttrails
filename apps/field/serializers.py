from rest_framework import serializers

from . import models


class FieldSerializer(serializers.ModelSerializer):
    """Serializer for field dababase model"""

    class Meta:
        model = models.Field
        fields = "__all__"


class FieldListSerializer(serializers.ModelSerializer):
    """Serializer to list fields with field code """

    class Meta:
        model = models.Field
        fields = ('id', 'farm', 'name', 'acreage','crop',)


# class FieldSustainabilitySerializer(serializers.ModelSerializer):
#     """Serializer to list fields with field code """

#     class Meta:
#         model = models.Field
#         fields = (
#             'water_saving', 'yield_per_acre',
#         )

class FieldListSerializerJson(serializers.ModelSerializer):
    """Serializer to list fields with field code """
    farm_name = serializers.ReadOnlyField(source='farm.name')
    grower_name= serializers.ReadOnlyField(source='grower.name')
   
 
 

    class Meta:
        model = models.Field
        fields = ('id','name','farm_name','grower_name','acreage','crop','get_polydata_count')