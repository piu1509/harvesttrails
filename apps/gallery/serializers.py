from rest_framework import serializers

from apps.gallery import models


class DocumentSerializer(serializers.ModelSerializer):
    """Serializes Gallery Model"""

    class Meta:
        model = models.Document
        fields = "__all__"


class GalleryDocumentSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, required=False)

    class Meta:
        model = models.Gallery
        fields = (
            'grower', 'farm', 'field', 'survey_type', 'year',
            'created_date', 'modified_date', 'documents'
        )

    def create(self, validated_data):
        grower = self.validated_data['grower']
        farm  = self.validated_data['farm']
        field  = self.validated_data['field']
        survey_type = self.validated_data['survey_type']
        year = self.validated_data['year']

        files = self.context['files']

        gallery = models.Gallery.objects.create(
            grower=grower, farm=farm, field=field,
            survey_type=survey_type, year=year
        )

        for file in files:
            models.Document.objects.create(gallery=gallery, file=file)

        return gallery
