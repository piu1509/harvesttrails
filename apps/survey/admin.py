from django.contrib import admin
from . import models

"""registering the database model for survey application in django admin panel"""


admin.site.register(models.SurveyInfo)
admin.site.register(models.Sustainability)

admin.site.register(models.Survey)
admin.site.register(models.SurveyType)
admin.site.register(models.QuestionAnswer)
admin.site.register(models.QuestionFile)
admin.site.register(models.ConsultantNotification)
admin.site.register(models.GrowerNotification)