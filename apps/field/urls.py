from django.urls import path

from apps.field import views

urlpatterns = [
    path('list/', views.FieldListView.as_view(), name='field-list'),
    path('get-varieties/<str:crop_code>/', views.get_varieties, name='get_varieties'),
    path('create/', views.FieldCreateView.as_view(), name='field-create'),
    path('<int:pk>/update/', views.FieldUpdateView.as_view(), name='field-update'),
#     path('<int:pk>/update/', views.fieldUpdateView, name='field-update'),
    path('<int:pk>/detail/', views.FieldDetailView.as_view(), name='field-detail'),
    path('<int:pk>/delete/', views.FieldDeleteView.as_view(), name='field-delete'),
    path('csv_field_create/', views.CsvFieldCreateView.as_view(), name='csv-field-create'),
    path('csv_field_mapping/<int:pk>', views.CsvFieldMappingView.as_view(), name='csv-field-mapping'),
    path('read_shape_file/', views.ReadShapeFile.as_view(), name='read_shape_file'),
    path('save_shape_file/', views.SaveShapeFile.as_view(), name='save-shape-file'),
    path('get_coordinates/', views.GetCoordinates.as_view(), name='get-coordinates'),
    path('eos-create-task/', views.EosCreateTask.as_view(), name='eos-create-task'),
    path('eos-task-status/', views.EosTaskStatus.as_view(), name='eos-task-status'),
    path('eos-task-search/', views.EosSearchTask.as_view(), name='eos-task-search'),
    path('eos-soilmoisture-create-task/', views.EosSoilmoistureCreateTask.as_view(),
         name='eos-soilmoisture-create-task'),
    path('eos-soilmoisture-data/', views.EosSoilMoistureData.as_view(), name='eos-soilmoisture-data'),
    path('eos-download-visual-data-create-task/', views.EosDownloadVisualDataCreateTask.as_view(),
         name='eos-download-visual-data-create-task'),
    path('field_location_map/vegetation/<int:pk>', views.FieldLocationMapVegetation.as_view(),
         name='field-location-map-vegetation'),
    path('field_location_map/moisture/<int:pk>', views.FieldLocationMapMoisture.as_view(),
         name='field-location-map-moisture'),
    path('EosTestTask/', views.EosTestTask.as_view(), name='EosTestTask'),
    path('eos-create-task-for-date-list/', views.EosCreateTasksForDateList.as_view(),
         name='eos-create-task-for-date-list'),
     #
     path('test/',views.test, name = 'test'),
     path('fieldActivity/',views.fieldActivity, name = 'fieldActivity'),
     path('fieldActivity_delete/<int:pk>',views.fieldActivity_delete, name = 'fieldActivity-delete'),
     path('upload_field_vegetation_csv',views.upload_field_vegetation_csv, name = 'upload_field_vegetation_csv'),
     path('field_csv_download',views.field_csv_download, name = 'field_csv_download'),
     # 19-06-23
     path('field_data_update/',views.field_data_update, name = 'field_data_update'),
     # 13-12-24
     path('update_field_2024/<str:pk>',views.update_field_2024, name = 'update_field_2024'),

]
