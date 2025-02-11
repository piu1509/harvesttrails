from django.contrib import admin
from .models import Farm, FarmGrouping, CsvToFarm

"""registering or database model for farm appplication in django admin panel"""
admin.site.register(Farm)
admin.site.register(FarmGrouping)
admin.site.register(CsvToFarm)