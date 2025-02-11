from django.db import IntegrityError

from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework import viewsets, response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from rest_framework.serializers import Serializer

from .serializers import (
    ConsultantSerializer, GrowerSerializer, GrowerListSerializer,
    ConsultantListSerializer
)
from .models import Consultant, Grower


class GrowerViewSet(viewsets.ViewSet):
    """Manages Grower in the database"""

    @action(methods=["post"], detail=False)
    def register(self, request, *args, **kwarsg):
        serializer = GrowerSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = {
                'grower': serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message' : "Grower Created Successfully",
            }
            return Response(data)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=['get'], detail=False, permission_classes = (IsAuthenticated,))
    def choices(self, request, *args, **kwargs):
        growers = request.user.grower
        serializer = GrowerListSerializer(growers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConsultantViewSet(viewsets.ViewSet):
    """Manages Consultant in the database"""

    @action(methods=['get'], detail=False)
    def choices(self, request, *args, **kwargs):
        consultants = Consultant.objects.all()
        serializer = ConsultantListSerializer(consultants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False)
    def add(self, request, *args, **kwarsg):
        serializer = ConsultantSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = {
                'consultant': serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message' : "Consultant Created Successfully",
            }
            return Response(data)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)


# class GrowerNotificationStatusViewSet(viewsets.ModelViewSet):
#     serializer_class = GrowerNotificationSerializer
#     authentication_class = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)

#     def get_queryset(self):
#         return GrowerNotification.objects.all().order_by('-created_date')

