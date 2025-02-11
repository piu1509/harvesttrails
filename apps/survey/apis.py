from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend

from apps.questions.models import Question
from apps.questions.serializers import QuestionOptionSerializer
from apps.survey.models import Survey, QuestionAnswer, ConsultantNotification, SurveyType, GrowerNotification, Sustainability
from apps.survey.serializers import (
    SurveySerializer, QuestionAnswerSerializer, ConsultantNotificationSerializer,
    ConsultantSurveyNotificationSerializer, SurveyTypeSerializer,
    GrowerSurveyNotificationSerializer, GrowerNotificationSerializer, SustainabilitySerializer
)

# from . import models
# from . import serializers


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['survey_type', 'grower', 'farm', 'field', 'year']

    def get_queryset(self):
        if self.action == "list":
            return Survey.objects.filter(grower=self.request.user.grower).order_by('-created_date')
        return Survey.objects.all().order_by('-created_date')


    @action(
        methods=['get'], detail=False, name='Survey Questions/Options',
        permission_classes= (IsAuthenticated,)
    )
    def questions(self, request, *args, **kwargs):
        questions = Question.objects.all().order_by('order')
        serializer = QuestionOptionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(
        methods=['get'], detail=False, name='Survey Types',
        permission_classes= (IsAuthenticated, )
    )
    def choices(self, request, *args, **kwargs):
        survey_types = SurveyType.objects.all()
        serializer = SurveyTypeSerializer(survey_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(methods=['post'], name='Submit Survey', detail=False)
    def submit(self, request, *args, **kwargs):
        _serializer = SurveySerializer(data=request.data)
        if _serializer.is_valid(raise_exception=True):
            _serializer.save()
            print(_serializer.validated_data)

            data = {
                'survey' : _serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message': 'Survey has been submitted successfully'
            }

            return Response(data)
        else:
            return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


    @action(
        methods=['patch'], detail=False, name='Accept Survey',
        permission_classes= (IsAuthenticated, )
    )
    def accept(self, request, *args, **kwargs):
        survey_id = self.request.query_params.get('survey_id')

        try:
            survey = Survey.objects.get(id=survey_id)
        except:
            survey = None

        if survey.is_accepted:
            return Response({'message': 'Survey is already accepted'})

        else:
            _serializer = SurveySerializer(survey, data=request.data, partial=True)
            if _serializer.is_valid(raise_exception=True):
                _serializer.save()
                data = {
                    'survey' : _serializer.data,
                    'statuscode' : status.HTTP_201_CREATED,
                    'message': 'Survey has been accepted'
                }
                return Response(data)
            else:
                return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


    @action(
        methods=['patch'], detail=False, name='Reject Survey',
        permission_classes= (IsAuthenticated, )
    )
    def reject(self, request, *args, **kwargs):
        survey_id = self.request.query_params.get('survey_id')

        try:
            survey = Survey.objects.get(id=survey_id)
        except:
            survey = None

        if survey.is_rejected:
            return Response({'message': 'Survey is already rejected'})

        else:
            _serializer = SurveySerializer(survey, data=request.data, partial=True)
            if _serializer.is_valid(raise_exception=True):
                _serializer.save()
                data = {
                    'survey' : _serializer.data,
                    'statuscode' : status.HTTP_201_CREATED,
                    'message': 'Survey has been rejected'
                }

                return Response(data)
            else:
                return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionAnswerViewSet(viewsets.ModelViewSet):
    queryset = QuestionAnswer.objects.all()
    serializer_class = QuestionAnswerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['survey',]


    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files', None)
        name = request.POST.get('name', None)
        latitude = request.POST.get('latitude', None)
        longitude = request.POST.get('longitude', None)


        data = {
            "survey": request.POST.get('survey', None),
            "question": request.POST.get('question', None),
            "option_chosen": request.POST.getlist('option_chosen', None)
            }

        context = {
            "files": files,
            'name': name,
            'latitude': latitude,
            'longitude':longitude
        }

        _serializer = QuestionAnswerSerializer(data=data, context=context)
        if _serializer.is_valid(raise_exception=True):
            _serializer.save()

            question_answer = {
                'survey' : _serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
                'message': 'Survey has been submitted successfully'
            }
            return Response(data=question_answer)
        else:
            return Response(data=_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultantNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultantSurveyNotificationSerializer
    queryset = Survey.objects.none()
    authentication_class = (TokenAuthentication,)


    @action(
        methods=['get'], detail=False, name='Consultant Notifications',
        permission_classes= (IsAuthenticated,)
    )
    def get(self, request, *args, **kwargs):
        surveys = Survey.objects.filter(grower=self.request.user.grower).order_by('-created_date')
        _serializer = ConsultantSurveyNotificationSerializer(surveys, many=True)
        return Response(_serializer.data, status=status.HTTP_200_OK)


    @action(
        methods=['patch'], detail=False, name='Read/Unread Consultant Notification',
        permission_classes= (IsAuthenticated,)
    )
    def read(self, request, *args, **kwargs):
        survey_id = self.request.query_params.get('survey_id')
        notification_id = self.request.query_params.get('notification_id')

        try:
            consultant_notification = ConsultantNotification.objects.get(
                id=notification_id, survey=survey_id
            )
        except:
            consultant_notification = None

        _serializer = ConsultantNotificationSerializer(
            consultant_notification, data=request.data, partial=True
        )
        if _serializer.is_valid(raise_exception=True):
            _serializer.save()

            data = {
                'consultant_notification' : _serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
            }

            if _serializer._validated_data['status'] == False:
                data['message'] = 'You have unread the consultant notification'
            else:
                data['message'] = 'You have read the consultant notification'

            return Response(data)
        else:
            return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


class GrowerNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = GrowerSurveyNotificationSerializer
    queryset = Survey.objects.none()
    authentication_class = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(
        methods=['get'], detail=False, name='Grower Notifications',
        permission_classes= (IsAuthenticated,)
    )
    def get(self, request, *args, **kwargs):
        surveys = Survey.objects.filter(grower=self.request.user.grower).order_by('-created_date')
        _serializer = GrowerSurveyNotificationSerializer(surveys, many=True)
        return Response(_serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['patch'], detail=False, name='Read/Unread Grower Notification',
        permission_classes= (IsAuthenticated,)
    )
    def read(self, request, *args, **kwargs):
        survey_id = self.request.query_params.get('survey_id')
        notification_id = self.request.query_params.get('notification_id')

        try:
            grower_notification = GrowerNotification.objects.get(
                id=notification_id, survey=survey_id
            )
        except:
            grower_notification = None

        _serializer = GrowerNotificationSerializer(
            grower_notification, data=request.data, partial=True
        )
        if _serializer.is_valid(raise_exception=True):
            _serializer.save()

            data = {
                'grower_notification' : _serializer.data,
                'statuscode' : status.HTTP_201_CREATED,
            }

            if _serializer._validated_data['status'] == False:
                data['message'] = 'You have unread the grower notification'
            else:
                data['message'] = 'You have read the grower notification'

            return Response(data)
        else:
            return Response(_serializer._errors, status=status.HTTP_400_BAD_REQUEST)


class SustainabilityViewSet(viewsets.ModelViewSet):
    queryset = Sustainability.objects.all()
    serializer_class = SustainabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['grower']


    @action(
        methods=['get'], detail=False, name='Sustainability Score'
    )
    def score(self, request, *args, **kwargs):
        sustainability = Sustainability.objects.all()
        serializer = SustainabilitySerializer(sustainability, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
