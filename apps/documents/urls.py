from django.urls import path
from apps.documents import views

urlpatterns = [
    path('folder_list/', views.FolderList.as_view(), name='folder-list'),
    path('get_folder/', views.GetFolder.as_view(), name='get-folder'),
    path('save_folder/', views.SaveFolder.as_view(), name='save-folder'),
    path('delete_folder/', views.DeleteFolder.as_view(), name='delete-folder'),
    path('upload_document_photo/', views.UploadDocumentPhoto.as_view(), name='upload-document-photo'),
    path('document_list/', views.DocumentList.as_view(), name='document-list'),
    path('update_document/<int:pk>/', views.UpdateUploadDocumentPhoto.as_view(), name='update-document'),
    path('document_delete/', views.DocumentDelete.as_view(), name='document-delete'),
    path('reports/', views.reports, name='reports'),
    path('reports_csv/<int:selectedGrower>/', views.reports_csv, name='reports_csv'),
    # Test Code ..................
    # path('reports_all/', views.reports_all, name='reports_all'),
    path('reports_csv_all/', views.reports_csv_all, name='reports_csv_all'),
    

]