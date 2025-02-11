from django.urls import path
from apps.storage import views

urlpatterns = [

    # path('create/', views.StorageCreateView.as_view(), name='storage-create'),
    path('create/', views.StorageCreateView, name='storage-create'),
    path('list/', views.StorageListView, name='storage-list'),
    path('<int:pk>/update/', views.StorageUpdateView, name='storage-update'),
    path('<int:pk>/delete/', views.storageDeleteView, name='storage-delete'),
    # path('AllStorageLocationMap/', views.AllStorageLocationMap, name='all-storage-location-map'),
    
    path('storage_feed_add/', views.storage_feed_add, name='storage_feed_add'),
    path('storage_feed_list/', views.storage_feed_list, name='storage_feed_list'),
    path('storage_feed_update/', views.storage_feed_update, name='storage_feed_update'),
    path('assign_feed_csv/', views.assign_storage_feed_csv, name='assign_feed_csv'),
]