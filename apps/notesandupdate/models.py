from django.db import models
from django.utils import timezone

# Create your models here.
class ReleaseNote(models.Model):
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.description}'

class UpcomingDate(models.Model):
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
    show_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.description}'

class HelpAndGuide(models.Model):
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    upload_file = models.FileField(upload_to='help_guide',null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title}'
