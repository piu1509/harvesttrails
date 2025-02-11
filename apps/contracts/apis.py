from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, response
from rest_framework.decorators import action
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend

from apps.field import serializers
from apps.field import models
from apps.core.utils import common_choice_response


class FieldViewSet(viewsets.ReadOnlyModelViewSet):
    """Handles Viewing and creating plots"""
    serializer_class = serializers.FieldSerializer
    queryset = models.Field.objects.all()
    authentication_class = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'id',]
    search_fields = ['name', 'id',]

    def get_queryset(self):
        """Returns queryset with farms associated with the user"""
        return models.Field.objects.filter(grower=self.request.user.grower)

    def get_serializer_class(self):
        """Returns appropiate serializer"""
        if self.action == "list":
            return serializers.FieldListSerializer
        return serializers.FieldSerializer

    @action(methods=["GET"], detail=False)
    def choices(self, request, *args, **kwargs):
        """Choices to select farms for a grower"""
        queryset = self.filter_queryset(self.get_queryset())
        return response.Response(common_choice_response(queryset=queryset))


