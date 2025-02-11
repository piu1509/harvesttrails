from django import forms


from . import models


class FarmForm(forms.ModelForm):

    class Meta:
        model = models.Farm
        labels = {
            "land_type": "Crop",
            "street": "Mailing Address 1",
            "village": "Address 2",
            "town": "City",
            "nutrien_account_id": "Nutrien Account Id",
            "county": "County/Parish", 
        }
        fields = (
            'name', 'cultivation_year', 'area', 'land_type', 'state', 'nutrien_account_id',
            'county', 'village', 'town', 'street', 'zipcode', 'grower'
        )
