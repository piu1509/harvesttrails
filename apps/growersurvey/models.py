from pyexpat import model
from django.db import models
from django.db.models.fields import TextField
from django.utils import timezone
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from rest_framework import status
from apps.core.validate import validate_year
from apps.core.utils import get_file_details
import json

# Create your models here.

class TypeSurvey(models.Model):
    name = models.CharField(max_length=255, null = False, blank = False)

    class Meta:
        verbose_name = "Type Survey"
        verbose_name_plural = "Type Surveys"

    def __str__(self):
        return f'{self.name}'

class NameSurvey(models.Model):
    typesurvey = models.ForeignKey(
        'growersurvey.TypeSurvey',
        on_delete=models.CASCADE,
        null=False, blank=False
    )
    surveyyear = models.CharField(max_length=255, null = False, blank = False)
    start_date = models.DateField(null=True, blank=True, verbose_name='Survey Start Date')
    end_date = models.DateField(null=True, blank=True, verbose_name='Survey End Date')

    

    class Meta:
        verbose_name = "Name Survey"
        verbose_name_plural = "Name Surveys"

    def __str__(self):
        return f'{self.typesurvey.name}, {self.surveyyear}'
   

class QuestionSurvey(models.Model):
    questionname = models.TextField(null = False, blank = False)
    namesurvey = models.ForeignKey(
        'growersurvey.NameSurvey',
        on_delete=models.CASCADE,
        null=False, blank=False
    )
    questiontotalscore = models.IntegerField(null=True, blank=True)
    questionorder = models.IntegerField(null=True, blank=True)
    selection_type = models.CharField(max_length=255, null = False, blank = False, default="radio")
    evidence_requird = models.BooleanField(default=False)
    evidence_descr = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.questionname}'

class OptionSurvey(models.Model):
    optionname = models.CharField(max_length=255, null = False, blank = False)
    questionsurvey = models.ForeignKey(
        'growersurvey.QuestionSurvey',
        on_delete=models.CASCADE,
        null=False, blank=False
    )
    optionscore =  models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.optionname} ({self.optionscore})'

class InputSurvey(models.Model):
    optionscore = models.IntegerField(null=True, blank=True)
    optionscore_ids = models.CharField(max_length=255, null = True, blank = True)
    questionsurvey = models.ForeignKey(
        'growersurvey.QuestionSurvey',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    grower = models.ForeignKey(
        'grower.Grower',
        on_delete=models.CASCADE,
        null=False, blank=True
    )
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE,null=True, blank=True)
    field = models.ForeignKey('field.Field', on_delete=models.CASCADE,null=True, blank=True)
    namesurvey = models.ForeignKey(
        'growersurvey.NameSurvey',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, null = True, blank = True)

    def __str__(self):
        return f"Question = {self.questionsurvey.questionname}, optionscore = {self.optionscore}"

    @property
    def get_evidence(self):
        evidence_data = list(Evidence.objects.filter(inputsurvey=self).values('file'))
        return json.dumps(evidence_data)

    @property
    def get_evidence_count(self):
        evidence_data_count = Evidence.objects.filter(inputsurvey=self).count()
        return evidence_data_count

    @property
    def get_options(self):
        if not self.optionscore_ids is None:
            opt_ids = []
            for opt_id in self.optionscore_ids.split(","):
                opt_ids.append(int(opt_id))
            option_data = OptionSurvey.objects.filter(questionsurvey=self.questionsurvey, id__in=opt_ids)
            return option_data
        
        option_data = OptionSurvey.objects.filter(questionsurvey=self.questionsurvey, optionscore=self.optionscore)
        return option_data


class Evidence(models.Model):
    inputsurvey = models.ForeignKey(
        'growersurvey.InputSurvey',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    file = models.FileField(upload_to='evidence/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.file}'

class SustainabilitySurvey(models.Model):
    grower = models.ForeignKey(
        'grower.Grower',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    namesurvey = models.ForeignKey(
        'growersurvey.NameSurvey',
        on_delete=models.CASCADE,
        null=False, blank=False
    )
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE,null=True, blank=True)
    field = models.ForeignKey('field.Field', on_delete=models.CASCADE,null=True, blank=True)
    surveyscore = models.IntegerField(null=True, blank=True)
    totalscore = models.IntegerField(null=True, blank=True)
    sustainabilityscore = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, null = True, blank = True)
    last_question = models.ForeignKey('growersurvey.QuestionSurvey', on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return f"{self.grower.name} ({self.grower.id}), {self.field.name} ({self.field.id}), Score = {self.sustainabilityscore}%, Status = {self.status}"


class SurveyCsvTable(models.Model):
    grower = models.ForeignKey(
        'grower.Grower',
        on_delete=models.CASCADE,
        null=False, blank=True
    )
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE,null=True, blank=True)
    field = models.ForeignKey('field.Field', on_delete=models.CASCADE,null=True, blank=True)
    namesurvey = models.ForeignKey(
        'growersurvey.NameSurvey',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    grower_idd = models.CharField(max_length=255, null = True, blank = True)
    grower_namee = models.CharField(max_length=255, null = True, blank = True)
    field_idd = models.CharField(max_length=255, null = True, blank = True)
    field_namee = models.CharField(max_length=255, null = True, blank = True)
    crop = models.CharField(max_length=255, null = True, blank = True)
    farm_idd = models.CharField(max_length=255, null = True, blank = True)
    farm_namee = models.CharField(max_length=255, null = True, blank = True)
    survey_name = models.CharField(max_length=255, null = True, blank = True)
    question_name = models.TextField(null = True, blank = True)
    ans_name = models.TextField(null = True, blank = True)
    ans_score = models.CharField(max_length=255, null = True, blank = True)
    attachment = models.CharField(max_length=255, null = True, blank = True)
    status = models.CharField(max_length=255, null = True, blank = True)
    created_date = models.CharField(max_length=255, null = True, blank = True)