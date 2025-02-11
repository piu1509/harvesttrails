from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from . import models
from . import serializers


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = models.Question.objects.all()
    serializer_class = serializers.QuestionOptionSerializer
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # filterset_fields = ['question_type',]
    # search_fields = ['question_type',]

    # def get_serializer_class(self):
    #     """Returns appropiate serializer"""
    #     if self.action == "list":
    #         return serializers.QuestionOptionSerializer
    #     return serializers.SurveyAnswerSerializer

    # @action(methods=['post'], detail=False)
    # def multiple_create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data, many=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response({'message': "Survey Submitted Successfully."}, status=status.HTTP_201_CREATED,
    #                     headers=headers)

