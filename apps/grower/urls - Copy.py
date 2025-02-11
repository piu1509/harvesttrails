from django.urls import path
from django.contrib.auth.decorators import login_required

from apps.grower import views

urlpatterns = [
	path('dashboard/',login_required(views.GorwerDashboardViewMain.as_view()),name='grower_dashboard'),
	path('dashboard1/',login_required(views.GorwerDashboardView1.as_view()),name='grower_dashboard1'),
	path('dashboard2/',login_required(views.GorwerDashboardView2.as_view()),name='grower_dashboard2'),
	path('chart1/',views.chart1,name='chart1'),
	path('chart2/',views.chart2,name='chart2'),
	path('chart2_detail/',views.chart2_detail,name='chart2_detail'),
	path('chart3/',views.chart3,name='chart3'),
	path('checklist_comparison/',views.checklist_comparison,name='checklist_comparison'),
	path('checklist_comparison_update/<int:pk>/',views.checklist_comparison_update,name='checklist_comparison_update'),
	path('grower_details_csv',views.grower_details_csv,name='grower_details_csv'),
	path('grower_dashboard_com/<str:web_get_grower>/',views.grower_dashboard_com,name='grower_dashboard_com'),
]

