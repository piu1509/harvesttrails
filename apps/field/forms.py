from django import forms
from django.forms.widgets import NumberInput
from django.forms.widgets import ChoiceWidget

from . import models

class FarmForm(forms.ModelForm):    

    def __init__(self, *args, **kwargs):
        
        super(FarmForm, self).__init__(*args, **kwargs)  
        crop_choices = [('', 'Select Crop')] + [(crop.code, crop.code) for crop in models.Crop.objects.all()]
        print(models.Crop.objects.all())
       
        self.fields['crop'] = forms.ChoiceField(
            choices=crop_choices,
            label="Select Crop",
            required=True,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['fsa_farm_number'].required = True
        self.fields['fsa_tract_number'].required = True
        self.fields['fsa_field_number'].required = True
    
    class Meta:
        model = models.Field
        fields = "__all__"

        widgets = {
            'burndown_chemical_date': NumberInput(attrs={'type': 'date'}),
            'plant_date': NumberInput(attrs={'type': 'date'}),
            'emergence_date': NumberInput(attrs={'type': 'date'}),
            'post_emergence_chemical_1_date': NumberInput(attrs={'type': 'date'}),
            'post_emergence_chemical_2_date': NumberInput(attrs={'type': 'date'}),
            'post_emergence_chemical_3_date': NumberInput(attrs={'type': 'date'}),
            'post_emergence_chemical_4_date': NumberInput(attrs={'type': 'date'}),
            'flood_date': NumberInput(attrs={'type': 'date'}),
            'awd_drydown_date': NumberInput(attrs={'type': 'date'}),
            'fungicide_micronutrients_date': NumberInput(attrs={'type': 'date'}),
            'insecticide_application_date': NumberInput(attrs={'type': 'date'}),
            'drain_date': NumberInput(attrs={'type': 'date'}),
            'sodium_chlorate_date': NumberInput(attrs={'type': 'date'}),
            'harvest_date': NumberInput(attrs={'type': 'date'}),
            'soil_sample_date': NumberInput(attrs={'type': 'date'}),
            'early_post_fert_date': NumberInput(attrs={'type': 'date'}),
            'foliar_fert_app_date': NumberInput(attrs={'type': 'date'}),
            'pre_flood_fert_date': NumberInput(attrs={'type': 'date'}),
            'post_flood_midseason_fert_date': NumberInput(attrs={'type': 'date'}),
            'post_flood_midseason_fert_date2': NumberInput(attrs={'type': 'date'}),
            'post_flood_midseason_fert_date3': NumberInput(attrs={'type': 'date'}),
            'boot_fertilizer_date': NumberInput(attrs={'type': 'date'}),
            'post_flood_midseason_fert_date2': NumberInput(attrs={'type': 'date'}),
            'post_flood_midseason_fert_date2': NumberInput(attrs={'type': 'date'}),
        }
