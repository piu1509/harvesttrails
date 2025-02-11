from rest_framework import serializers

from . import models


class OptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Option
        fields = ('id', 'order', 'text', 'points', )


class QuestionOptionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = models.Question
        fields = ['id', 'category', 'type', 'survey_type', 'order', 'text', 'max_points', 'options']

