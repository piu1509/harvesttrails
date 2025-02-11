from rest_framework import serializers

from . import models


class ContractsSerializer(serializers.ModelSerializer):
    """Serializer for field dababase model"""

    class Meta:
        model = models.Contracts
        fields = "__all__"
