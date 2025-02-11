from django.urls import path
from apps.survey import views


urlpatterns = [
    path('survey/', views.SurveyListView.as_view(), name='survey'),
    path('sustainability/', views.SustainabilityListView.as_view(), name='sustainability'),
    path('option/create/', views.OptionCreateView.as_view(), name='option-create'),
    path('option/<int:pk>/update/', views.OptionUpdateView.as_view(), name='option-update'),
    path('surveyreject/',views.SurveyRejectNotification.as_view(), name="survey-reject"),
    path('surveychartdata/',views.surveyChartData,name='survey-chart-data'),
    #path('statusupdate/',views.SurveyStatusUpdate.as_view(),name='survey-status-update'),
    path('load_farms/',views.LoadFarms.as_view(),name='load-farm'),
    path('load_field/',views.LoadFields.as_view(),name='load-field'),
    path('loadYears/',views.LoadYears.as_view(),name='load-year'),
    path('loadpopup/',views.LoadPopup.as_view(),name='load-popup'),
    path('getSurveyData/',views.GetSurveyData.as_view(),name='get-survey-data'),
    path('loadquestions/',views.LoadQuestions.as_view(),name='load-questions'),
    path('survey_score_type/',views.GetSurveyScoreType.as_view(),name='survey-score-type'),
    # path('question/<int:pk>/update/', views.QuestionUpdateView.as_view(), name='question-update'),
]