from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.TypeSurvey)
admin.site.register(models.NameSurvey)
admin.site.register(models.QuestionSurvey)
admin.site.register(models.OptionSurvey)
admin.site.register(models.InputSurvey)
admin.site.register(models.SustainabilitySurvey)
admin.site.register(models.Evidence)
