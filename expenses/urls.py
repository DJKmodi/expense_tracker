from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    path('expenses/', views.expense_list_view, name='expenses'),
    path('expenses/add/', views.expense_add_view, name='expense_add'),
    path('expenses/<int:pk>/', views.expense_detail_view, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.expense_edit_view, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    
    path('incomes/add/', views.income_add_view, name='income_add'),
    path('incomes/<int:pk>/edit/', views.income_edit_view, name='income_edit'),
    path('incomes/<int:pk>/delete/', views.income_delete_view, name='income_delete'),
    
    path('reports/', views.reports_view, name='reports'),
    path('reports/download-pdf/', views.download_report_pdf_view, name='download_report_pdf'),
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/category/add/', views.admin_category_add_view, name='admin_category_add'),
]


