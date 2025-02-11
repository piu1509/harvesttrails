from django.contrib import admin


from import_export import resources
from import_export.admin import ImportExportModelAdmin

from . import models


class OptionInline(admin.TabularInline):
	model = models.Option

class QuestionAdmin(ImportExportModelAdmin):
	inlines = [OptionInline]


admin.site.register(models.Option, ImportExportModelAdmin)
admin.site.register(models.Question, QuestionAdmin)


class QuestionResource(resources.ModelResource):
	class Meta:
		model = models.Question
		import_id_fields = ('id',)
		fields = ('id', 'category', 'type', 'order', 'text', 'max_points',)


class OptionResource(resources.ModelResource):
	class Meta:
		model = models.Option
		import_id_fields = ('id',)
		fields = ('id', 'question', 'order', 'text', 'points', 'is_active')

