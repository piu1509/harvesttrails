from django.db.models import fields
from rest_framework import serializers

from . import models


class SurveyTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SurveyType
        fields = ('id', 'name', )


class QuestionFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.QuestionFile
        fields = ('question_answer', 'file', 'name', 'latitude', 'longitude' )


class SurveyQuestionAnswerSerializer(serializers.ModelSerializer):
    files = QuestionFileSerializer(many=True, required=False)

    class Meta:
        model = models.QuestionAnswer
        fields = ('id', 'survey', 'question', 'option_chosen', 'files')


class SurveySerializer(serializers.ModelSerializer):
    question_answers = SurveyQuestionAnswerSerializer(many=True, read_only=True)
    grower_name = serializers.CharField(source='grower.name', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)

    class Meta:
        model = models.Survey
        fields = (
            'id', 'grower', 'grower_name', 'survey_type', 'farm',
            'farm_name', 'field', 'field_name', 'year', 'is_accepted',
            'is_rejected', 'comment', 'sustainability_score', 'question_answers',
        )


class QuestionAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.QuestionAnswer
        fields = ('id', 'survey', 'question', 'option_chosen',)


    def create(self, validated_data):
        survey = self.validated_data['survey']
        question  = self.validated_data['question']
        options = self.validated_data['option_chosen']

        files = self.context['files']
        name = self.context['name']
        latitude = self.context['latitude']
        longitude = self.context['longitude']

        question_answer = models.QuestionAnswer.objects.create(
            survey=survey, question=question
        )

        for option in options:
            question_answer.option_chosen.add(option)

        for file in files:
            models.QuestionFile.objects.create(
                question_answer=question_answer, file=file,
                name=name, latitude=latitude, longitude=longitude
            )

        return question_answer


class ConsultantNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ConsultantNotification
        fields = ('id', 'survey', 'text', 'status', 'created_date', )


class ConsultantSurveyNotificationSerializer(serializers.ModelSerializer):
    consultant_notifications = ConsultantNotificationSerializer(many=True, required=False)
    grower_name = serializers.CharField(source='grower.name', read_only=True)


    class Meta:
        model = models.Survey
        fields = (
            'id', 'survey_type', 'grower', 'grower_name', 'farm', 'field',
            'year', 'is_accepted', 'is_rejected', 'created_date', 'comment',
            'consultant_notifications',
        )


class GrowerNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.GrowerNotification
        fields = ('id', 'survey', 'text', 'status', 'created_date', )


class GrowerSurveyNotificationSerializer(serializers.ModelSerializer):
    grower_notifications = GrowerNotificationSerializer(many=True, required=False)
    grower_name = serializers.CharField(source='grower.name', read_only=True)

    class Meta:
        model = models.Survey
        fields = (
            'id', 'survey_type', 'grower', 'grower_name', 'farm', 'field', 'year',
            'is_accepted', 'is_rejected', 'created_date', 'modified_date',
            'grower_notifications',
        )


class SustainabilitySerializer(serializers.ModelSerializer):
    grower_name = serializers.CharField(source='grower.name', read_only=True)

    class Meta:
        model = models.Sustainability
        fields = ('id', 'land_saving', 'water_saving', 'co2_equivalents_reduced', 'grower', 'grower_name')
