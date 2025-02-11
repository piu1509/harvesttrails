from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_year(value):
    if value < 2000 or len(str(value)) != 4:
        raise ValidationError(
            _('%(value)s is not an valid year'),
            params={'value': value},
        )


def validate_zipcode(value):
    value = str(value)
    if len(value) != 5:
        raise ValidationError(
            _('%(value)s is invalid, 5 digits required!'),
            params={'value': value},
        )

