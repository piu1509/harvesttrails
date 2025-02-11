from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import viewsets, response
from rest_framework import filters

from django_filters.rest_framework import DjangoFilterBackend

from apps.farms import serializers
from apps.farms.models import Farm
from apps.core.utils import common_choice_response


class FarmViewSet(viewsets.ReadOnlyModelViewSet):
    """API Viewset for Farm model to get farm list, farm details"""
    authentication_class = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name',]
    search_fields = ['name',]

    def get_queryset(self):
        """Returns queryset with farms associated with the user"""
        if self.action == "list":
            return Farm.objects.annotate(field_count=Count("fields")).annotate(total_area=Sum('fields__acreage')).filter(grower=self.request.user.grower)
        elif self.request.user.is_superuser:
            return Farm.objects.all()
        return Farm.objects.filter(grower=self.request.user.grower)
        

    def get_serializer_class(self):
        """Returns appropiate serializer"""
        if self.action == "list":
            return serializers.FarmListSerializer
        return serializers.FarmSerializer

    @action(methods=["GET"], detail=False)
    def choices(self, request, *args, **kwargs):
        """choices to select farms for a grower"""
        queryset = self.filter_queryset(self.get_queryset())
        return response.Response(common_choice_response(queryset=queryset))
    
    @action(methods=["GET"], detail=False)
    def farm_details(self, request, *args, **kwargs):
        farm = get_object_or_404(self.get_queryset())
        serializer = serializers.FarmDetailSerializer(farm)
        return response.Response(serializer.data)
