from django import forms
from django.forms.widgets import NumberInput
from django.forms.widgets import ChoiceWidget

from . import models
from .models import *
class StorageForm(forms.ModelForm):
    class Meta:
        model = Storage
        fields = "__all__"

        widgets = {
            'grower': forms.Select(attrs={'class':'form-select'}),
            'upload_type': forms.Select(attrs={'class':'form-select'}),
        }
        