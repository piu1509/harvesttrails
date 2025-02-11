from .models import *
from django import forms

class DistributorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DistributorForm, self).__init__(*args, **kwargs)
        self.fields['entity_name'].required = True
        self.fields['location'].required = True

    class Meta:
        model = Distributor
        fields = [
            'entity_name', 'warehouse', 'location', 'latitude', 'longitude'
        ]
        widgets = {
            'entity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,  
                'cols': 30  
            }),
            'latitude': forms.TextInput(attrs={'class': 'form-control'}),
            'longitude': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class WarehouseForm(forms.ModelForm):
    distributor = forms.ModelMultipleChoiceField(
        queryset=Distributor.objects.all(),
        required=False, 
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}), 
        label="Select Distributor"
    )
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Select Customers"
    )
    def __init__(self, *args, **kwargs):
        super(WarehouseForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['location'].required = True

        if self.instance.pk:
            self.fields['distributor'].initial = self.instance.distributor_set.all()  
            self.fields['customers'].initial = self.instance.customer_set.all()           

    class Meta:
        model = Warehouse
        fields = ['name', 'location', 'latitude', 'longitude', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'cols': 30
            }),
            'latitude': forms.TextInput(attrs={'class': 'form-control'}),
            'longitude': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomerForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['location'].required = True        

    class Meta:
        model = Customer
        fields = [
            'name', 'location', 'latitude', 'longitude',
            'credit_terms', 'billing_address', 'shipping_address',
            'is_tax_payable', 'tax_percentage','warehouse'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'cols': 30
            }),
            'latitude': forms.TextInput(attrs={'class': 'form-control'}),
            'longitude': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_terms': forms.Select(attrs={'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'cols': 30
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 1,
                'cols': 30
            }),
            'is_tax_payable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Tax percentage if applicable'
            }),
            'warehouse': forms.Select(attrs={'class': 'form-control'}, choices=[('', 'Select Warehouse')]),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_tax_payable = cleaned_data.get("is_tax_payable")
        tax_percentage = cleaned_data.get("tax_percentage")

        if is_tax_payable and not tax_percentage:
            self.add_error('tax_percentage', "Tax percentage is required when tax is payable.")

        if not is_tax_payable:
            cleaned_data['tax_percentage'] = None

        return cleaned_data
    
