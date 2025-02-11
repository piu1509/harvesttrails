import django_filters

from apps.grower.models import Grower


class GrowerFilter(django_filters.FilterSet):
    """filter class to filter gower for grower API"""

    class Meta:
        model = Grower
        fields = {
            'name': ['iexact', ],
            'email': ['iexact', ],
            'date_created': ['year',],
        }
