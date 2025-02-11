from django import forms
from django.forms import ClearableFileInput, widgets

from . import models


class GalleryForm(forms.ModelForm):

    class Meta:
        model = models.Gallery
        fields = ('grower', 'farm', 'field', 'survey_type', 'year')


class FileForm(forms.ModelForm):

    class Meta:
        model = models.Document
        fields = ('file', )
        widgets = {
			'file' : ClearableFileInput(attrs={'multiple': False})
		}
