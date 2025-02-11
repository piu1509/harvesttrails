from django.db import models
from django.utils import timezone
import os

# Create your models here.
class DocumentFolder(models.Model):
    name = models.CharField(unique=True, max_length=150, null=False, blank=False)
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=False, blank=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'


class DocumentFile(models.Model):
    file = models.FileField(upload_to='document/',null=True, blank=True)
    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE, null=False, blank=False)
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE, null=False, blank=False)
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE,null=True, blank=True)
    field = models.ForeignKey('field.Field', on_delete=models.CASCADE,null=True, blank=True)
    corp_year = models.CharField(max_length=150, null=True, blank=True)
    tag = models.TextField(null=True, blank=True)
    keyword = models.TextField(null=False, blank=False)
    survey_type = models.ForeignKey('growersurvey.TypeSurvey', on_delete=models.CASCADE, null=False, blank=False)
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=False, blank=False)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.file}'

    def filename(self):
        return os.path.basename(self.file.name)