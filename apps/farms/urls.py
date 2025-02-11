from django.urls import path
from apps.farms import views


urlpatterns = [
    path('farms_list/', views.FarmListView.as_view(), name='farm-list'),
    path('farms_location/', views.farmlocationview, name='farm-location'),
    path('farms_create/', views.FarmCreateView.as_view(), name='farm-create'),
    path('farms_list/<int:pk>/update/', views.FarmUpdateView.as_view(), name='farm-update'),
    path('farms_list/<int:pk>/delete/', views.FarmDeleteView.as_view(), name='farm-delete'),
    path('farms_list/<int:pk>/detail/', views.FarmDetailView.as_view(), name='farm-detail'),
    path('grouping/', views.FarmGroupingListView.as_view(), name='grouping'),
    path('grouping/create/', views.FarmGroupingCreateView.as_view(), name='grouping-create'),
    path('grouping/<int:pk>/update/', views.FarmGroupingUpdateView.as_view(), name='grouping-update'),
    path('grouping/<int:pk>/delete/', views.FarmGroupingDeleteView.as_view(), name='grouping-delete'),
    path('csv_farms_create/', views.CsvFarmCreateView.as_view(), name='csv-farm-create'),
    path('csv_farm_mapping/<int:pk>/',views.CsvFarmMappingView.as_view(),name='csv-farm-mapping'),
    path('farms_location_map_view/<int:pk>/<int:grower_id>/', views.FarmLocationMap.as_view(), name='farm-location-map-view'),
    path('all_farms_location_map_view/<int:grower_id>/', views.AllFarmLocationMap.as_view(), name='all-farm-location-map-view'),

    path('crop_management_list/', views.crop_management, name="crop_management_list"),
    path('create_crop/', views.create_crop, name="create_crop"),
    path('edit_crop/<int:crop_id>/', views.edit_crop, name='edit_crop'),
    path('view_crop/<int:crop_id>/', views.view_crop, name='view_crop'),
    path('delete-crop/<int:crop_id>/', views.delete_crop, name='delete_crop'),

]