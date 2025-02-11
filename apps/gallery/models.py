'''Models for Gallery app'''

import os
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib import messages

from PIL import Image
from main.settings import MEDIA_ROOT

from apps.survey.models import SURVEY_CHOICES
from apps.core.validate import validate_year
from apps.core.utils import get_file_details


#get file extension
def get_file_extension(file_name=None):
    '''For getting file name extension'''

    if isinstance(file_name,str):
        flag = 0
        for i in range(len(file_name),0,-1):
            if file_name[i-1] == '.':
                ext_index = i-1
                flag = 1
                break
        if flag == 1:
            return file_name[ext_index:]
    return None

def get_file_name_without_extension(full_path = None):
    '''For getting file name without extension'''

    if full_path is not None:
        file_name = (os.path.basename(full_path).split('.')[0]).split('~~')[0]
        if len(file_name) > 50:
            file_name = file_name[:50]
        return file_name
    return ''

def rename_file():
    '''For renaming file with date time stamp'''

    dtime = str(datetime.now())
    dtime = dtime.replace(" ","-").replace(":","-").replace(".","-")
    dtime = '~~' + dtime[:22]
    return dtime


class Gallery(models.Model):
    """Database model for gallery"""
    grower = models.ForeignKey('grower.Grower', on_delete=models.CASCADE)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE)
    field = models.ForeignKey("field.field", on_delete=models.CASCADE)
    survey_type = models.ForeignKey(
        "survey.SurveyType", on_delete=models.CASCADE, verbose_name='Survey Type'
    )
    year = models.PositiveSmallIntegerField(
        validators=[validate_year], verbose_name="Year"
    )
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Gallery"


    def form_valid(self, form):
        """overriding this method to get a message"""
        messages.success(self.request, f'Files Uploaded Successfuly!')
        return super().form_valid(form)


    def __str__(self):
        """Returns string representation for gallery"""
        return f'{self.grower.name}:{self.farm.name}: {self.field.name}'


    # def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

    #     '''Overriding the save method'''
    #     super().save(force_insert, force_update, using, update_fields)
    #     if self.image.name is not None:
    #         try:
    #             os.chdir(MEDIA_ROOT)
    #             new_file_name = 'survey_images/'+ get_file_name_without_extension(\
    #                 str(self.image.name)) + rename_file() + \
    #                 get_file_extension(str(self.image.name))
    #             os.rename(str(self.image.name),new_file_name)
    #             self.image.name = new_file_name
    #             super().save()
    #         except:
    #             pass

    #     if self.file.name is not None:
    #         try:
    #             os.chdir(MEDIA_ROOT)
    #             new_file_name = 'survey_files/'+ get_file_name_without_extension(\
    #                 str(self.file.name)) + rename_file() + get_file_extension(\
    #                 str(self.file.name))
    #             os.rename(str(self.file.name),new_file_name)
    #             self.file.name = new_file_name
    #             super().save()
    #         except:
    #             pass

    #     try:
    #         img = Image.open(self.image.path)

    #         if img.height > 300 or img.width > 300:
    #             output_size = (300, 300)
    #             img.thumbnail(output_size)
    #             img.save(self.image.path)
    #     except:
    #         pass



class Document(models.Model):
    gallery = models.ForeignKey('Gallery', on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='survey_files/')
    is_image = models.BooleanField(default=True)
    file_name = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.CharField(max_length=200, null=True, blank=True)
    longitude = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if self.file.name.lower().endswith(
            ('jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'bmp')
        ):
            self.is_image = True
        else:
            self.is_image = False

        if 'AgrStringFile' in self.file.name:
            file_details = get_file_details(self.file.name)
            print(file_details)
            self.latitude = file_details['latitude']
            self.longitude = file_details['longitude']
            self.file_name = file_details['fileName']
        super(Document, self).save(*args, **kwargs)


    def __str__(self):
        """Returns string representation for file"""
        return f'{self.file.url}'




