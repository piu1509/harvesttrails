from pyexpat import model
from django import forms
from . import models

def crop_choices():
    from apps.field.models import Crop
    crops = Crop.objects.all()
    return [(crop.code, crop.name) for crop in crops]

VARIETY_CHOICES = (
                ('DG-263L', 'DG-263L'),
                ('DG 2425 XF', 'DG 2425 XF'),
                ('DG 3450 B2XF', 'DG 3450 B2XF'),
                ('DG 3470 B3XF', 'DG 3470 B3XF'),
                ('DG 3570 B3XF', 'DG 3570 B3XF'),
                ('DG 3635 B2XF', 'DG 3635 B2XF'),
                ('DG 3544 B2XF', 'DG 3544 B2XF'),
                ('DG 3651NR B2XF', 'DG 3651NR B2XF'),
                ('DG 3109 B2XF', 'DG 3109 B2XF'),
                ('DG 3387 B3XF', 'DG 3387 B3XF'),
                ('DG 3421 B3XF', 'DG 3421 B3XF'),
                ('DG H929 B3XF', 'DG H929 B3XF'),
                ('DG 3555 B3XF', 'DG 3555 B3XF'),
                ('DG 3402 B3XF', 'DG 3402 B3XF'),
                ('DG H959 B3XF', 'DG H959 B3XF'),
                ('DG 3469 B3XF', 'DG 3469 B3XF'),
                ('DG 3615 B3XF', 'DG 3615 B3XF'),
                ('DG P224 B3XF', 'DG P224 B3XF'),
                ('DG 3385 B2XF', 'DG 3385 B2XF'),
                ('DG 3422 B3XF', 'DG 3422 B3XF'),
                ('DG 3799 B3XF', 'DG 3799 B3XF'),
            )
class ProcessorForm(forms.ModelForm):
    main_number = forms.IntegerField()
    main_fax=forms.IntegerField()
    main_email = forms.CharField()
    # contact_phone=forms.IntegerField()
    # contact_fax=forms.IntegerField()
    # contact_email=forms.EmailField()

    def __init__(self, *args, **kwargs):
        super(ProcessorForm, self).__init__(*args, **kwargs)
        self.fields['fein'].required = True
        self.fields['entity_name'].required = True
        self.fields['billing_address'].required = True
        # self.fields['contact_name'].required = True
        # self.fields['main_number'].required = False
        # self.fields['main_fax'].required = False
        # self.fields['contact_phone'].required = False
        # self.fields['contact_fax'].required = False

    class Meta:
        model = models.Processor
        # labels = {
        #     "fein": "FEIN",
        #     "entity_name": "Entity Name",
        #     "billing_address": "Billing Address",
        #     "shipping_address": "Shipping Address",
        #     "main_number": "Main Number",
        #     "main_fax": "Main Fax",
        #     "website": "Website",
        #     "contact_name": "Contact Name",
        #     "contact_email": "Contact Email",
        #     "contact_phone": "Contact Phone",
        #     "contact_fax": "Contact Fax",
        # }
        fields = [
            'fein', 'entity_name', 'billing_address', 'shipping_address', 'main_number', 'main_fax', 'main_email',
            'website'
        ]
        widgets = {
            'billing_address': forms.TextInput(attrs={'class': 'form-control',}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control',}),
            'website': forms.TextInput(attrs={'class': 'form-control',}),
            
        }


class LocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['upload_type'].required = True
        self.fields['processor'].required = True
    class Meta:
        model = models.Location
        fields = '__all__'
        widgets = {
            'upload_type': forms.Select(attrs={'class': 'form-select',}),
        }

class GrowerShipmentForm(forms.Form):
    crop = forms.ChoiceField(choices=crop_choices(),widget=forms.Select(attrs={'class': 'form-control'}),required=True)
    variety = forms.ChoiceField(choices=VARIETY_CHOICES,widget=forms.Select(attrs={'class': 'form-control'}),required=True)
    