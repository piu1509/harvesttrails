from django.db import models
from django.db.models.fields import TextField
from django.utils import timezone
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from rest_framework import status
from apps.core.validate import validate_year
from apps.core.utils import get_file_details

class Sustainability(models.Model):
    """Database model for sustainability"""
    grower = models.ForeignKey(
        'grower.Grower',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    land_saving = models.IntegerField(null=True, blank=True)
    water_saving = models.IntegerField(null=True, blank=True)
    co2_equivalents_reduced = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Sustainability"
        verbose_name_plural = "Sustainability"

    def __str__(self):
        return f'{self.grower.name}'


class SurveyInfo(models.Model):
    '''Model for saving survey related information like survey year
    survey date approve status etc
    This model is managed by signals.py
    and SurveyStatusUpdate & SustainabilityListView in views.py'''
    grower = models.ForeignKey(
        'grower.Grower',
        on_delete=models.CASCADE
    )
    farm = models.ForeignKey(
        'farms.Farm',
        on_delete=models.CASCADE
    )
    field = models.ForeignKey(
        'field.field',
        on_delete=models.CASCADE
    )
    year = models.IntegerField(validators=[validate_year])
    survey_date = models.DateTimeField() #Last updated survey data and time auto_now=True
    approve_status = models.BooleanField(default=False)
    approved_date = models.DateTimeField(null=True, blank=True)
    cons_status = models.BooleanField(default=False) #consultant_notification_status

    class Meta:
        verbose_name = "Survey Info"
        verbose_name_plural = "Survey Info"


    def __str__(self):
        '''String representation for object'''
        return f'{self.grower} - {self.farm} - {self.field} - Year : {self.year}'


SURVEY_CHOICES = (
    ('Entry Survey', 'Entry Survey'),
    ('Complete Survey', 'Complete Survey'),
    ('Sales Survey', 'Sales Survey'),
)

class SurveyType(models.Model):
    name = models.CharField(max_length=255, choices=SURVEY_CHOICES)

    class Meta:
        verbose_name = "Survey Type"
        verbose_name_plural = "Survey Types"

    def __str__(self):
        return f'{self.name}'


class Survey(models.Model):
    survey_type = models.ForeignKey('SurveyType', on_delete=models.CASCADE)
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE)
    field = models.ForeignKey('field.field', on_delete=models.CASCADE)
    year = models.IntegerField(validators=[validate_year])
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=True)
    comment = models.TextField(default='No Comments')
    sustainability_score = models.IntegerField(null=True, blank=True)


    class Meta:
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"


    def get_score(self):
        """this method gets all the options of a questions and sort them via order"""
        questions = self.question_answers.aggregate(max_points=Sum('question__max_points'))
        options = self.question_answers.aggregate(farm_points=Sum('option_chosen__points'))
        if questions['max_points'] is not None and options['farm_points'] is not None:
            score = round((options['farm_points']/questions['max_points'])*100, 2)
        else:
            score = None
        return score


    def save(self, *args, **kwargs):
        self.sustainability_score = self.get_score()
        super(Survey, self).save(*args, **kwargs)


    def __str__(self):
        return f'ID: {self.id}: {self.survey_type.name} for \
            Grower: {self.grower.name}, Farm: {self.farm.name}, Field: {self.field.name} '


class QuestionAnswer(models.Model):
    survey = models.ForeignKey(
        'Survey', on_delete=models.CASCADE, related_name='question_answers'
    )
    question = models.ForeignKey('questions.question', on_delete=models.CASCADE)
    option_chosen= models.ManyToManyField('questions.option')

    class Meta:
        verbose_name = "Question Answer"
        verbose_name_plural = "Question Answers"


    def __str__(self):
        return f'{self.survey.survey_type.name} for {self.survey.grower.name} \
            Grower Question: {self.question.id}: {self.question.text}, '


class QuestionFile(models.Model):
    question_answer = models.ForeignKey('QuestionAnswer', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='survey_files/', null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.CharField(max_length=200, null=True, blank=True)
    longitude = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Question File"
        verbose_name_plural = "Question Files"

    def __str__(self):
        return f'{self.id}: File of Question: {self.question_answer.question.text}'

    def save(self, *args, **kwargs):
        if 'AgrStringFile' in self.file.name:
            print(self.file.name)
            file_details = get_file_details(self.file.name)
            print(file_details)
            self.latitude = file_details['latitude']
            self.longitude = file_details['longitude']
            self.name = file_details['fileName']
        super(QuestionFile, self).save(*args, **kwargs)


class ConsultantNotification(models.Model):
    survey = models.ForeignKey(
        'Survey', on_delete=models.CASCADE, related_name='consultant_notifications'
    )
    text = models.TextField()
    status = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Consultant Notification"
        verbose_name_plural = "Consultant Notifications"


    def __str__(self):
        return f'{self.text}'


class GrowerNotification(models.Model):
    survey = models.ForeignKey(
        'Survey', on_delete=models.CASCADE, related_name='grower_notifications'
    )
    text = models.TextField()
    status = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Grower Notification"
        verbose_name_plural = "Grower Notifications"


    def __str__(self):
        return f'{self.text}'

