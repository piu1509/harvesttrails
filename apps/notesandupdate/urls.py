from django.urls import path

from apps.notesandupdate import views

urlpatterns = [
    path('release_notes_list/', views.ReleaseNotesList.as_view(), name='release-notes-list'),
    path('upcoming_date_list/', views.UpcomingDateList.as_view(), name='upcoming-date-list'),
    path('release_notes_create/', views.ReleaseNotesCreate.as_view(), name='release-notes-create'),
    path('release_notes_create/save/', views.ReleaseNotesCreateSave, name='release-notes-create-save'),
    path('upcoming_date_create/', views.UpcomingDateCreate.as_view(), name='upcoming-date-create'),
    path('upcoming_date_create/save/', views.UpcomingDateCreateSave, name='upcoming-date-create-save'),
    path('release_notes_update/<int:pk>/', views.ReleaseNotesUpdate.as_view(), name='release-notes-update'),
    path('release_notes_update/save/', views.ReleaseNotesUpdateSave, name='release-notes-update-save'),
    path('upcoming_date_update/<int:pk>/', views.UpcomingDateUpdate.as_view(), name='upcoming-date-update'),
    path('upcoming_date_update/save/', views.UpcomingDateUpdateSave, name='upcoming-date-update-save'),
    path('upcoming_date_delete/', views.UpcomingDateDelete, name='upcoming-date-delete'),
    path('release_notes_delete/', views.ReleaseNotesDelete, name='release-notes-delete'),
    # 27/12/22
    path('HelpAndGuideCreate/', views.HelpAndGuideCreate, name='HelpAndGuideCreate'),
    path('HelpAndGuideList/', views.HelpAndGuideList, name='HelpAndGuideList'),
    path('HelpAndGuideEdit/<int:pk>/', views.HelpAndGuideEdit, name='HelpAndGuideEdit'),
    path('HelpAndGuideDelete/', views.HelpAndGuideDelete, name='HelpAndGuideDelete'),
    path('HelpAndGuideView/', views.HelpAndGuideView, name='HelpAndGuideView'),
    path('HelpAndGuideDetails/<int:pk>', views.HelpAndGuideDetails, name='HelpAndGuideDetails'),
]