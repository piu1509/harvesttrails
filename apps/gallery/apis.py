from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, response
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from apps.gallery import serializers
from apps.gallery import models
from apps.core.utils import common_choice_response


class GalleryViewSet(viewsets.ModelViewSet):
    """Handles uploading, viewing, deleting and updating files and photos"""
    queryset = models.Gallery.objects.none()
    serializer_class = serializers.GalleryDocumentSerializer
    authentication_class = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['grower', 'farm', 'field', 'survey_type', 'year']


    # @action(methods=['get'], detail=False, permission_classes = (IsAuthenticated,))
    # def files(self, request, *args, **kwargs):
    #     if request.user.is_superuser:
    #         files = models.Gallery.objects.all()
    #     else:
    #         files = models.Gallery.objects.filter(grower=self.request.user.grower)
    #     serializer = serializers.GalleryDocumentSerializer(files, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return models.Gallery.objects.all()
        else:
            return models.Gallery.objects.filter(grower=self.request.user.grower)


    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files', None)

        data = {
            "grower": request.POST.get('grower', None),
            "survey_type": request.POST.get('survey_type', None),
            "farm": request.POST.get('farm', None),
            "field": request.POST.get('field', None),
            "year": request.POST.get('year', None)
            }

        context = {
            "files": files,
        }

        _serializer = serializers.GalleryDocumentSerializer(data=data, context=context)
        if _serializer.is_valid(raise_exception=True):
            _serializer.save()

            gallery_data = {
                'gallery' : _serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message': 'Files have been uploaded successfully'
            }
            return Response(data=gallery_data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(methods=['post'], detail=False)
        # def save(self, request, *args, **kwargs):
        #     serializer = serializers.GalleryDocumentSerializer(data=request.data)
        #     if serializer.is_valid(raise_exception=True):
        #         serializer.save()
        #         data = {
        #             'gallery' : serializer.data,
        #             'statuscode' : status.HTTP_201_CREATED,
        #             'message': 'File has been uploaded successfully'
        #         }
        #         return Response(data)
        #     else:
        #         return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)
