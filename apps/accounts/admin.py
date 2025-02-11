from django.contrib import admin

from import_export import resources
from import_export.admin import ImportExportModelAdmin

from . import models

"""registering the database model for accounts appplication in django admin panel"""

admin.site.register(models.User)
admin.site.register(models.Role)
admin.site.register(models.ShowNotification)
admin.site.register(models.Permission, ImportExportModelAdmin)
admin.site.register(models.SubSuperUser)


class PermissionResource(resources.ModelResource):
	"""Class for import-export library to import custom permission file to database from django admin panel"""
	class Meta:
		model = models.Permission
		import_id_fields = ('id',)
		fields = ('id', 'name', 'display', )

admin.site.register(models.VersionUpdate)
