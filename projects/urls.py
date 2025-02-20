from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),

    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),


    # Project Management
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/add-terms/', views.add_terms_rewards, name='add_terms_rewards'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    
    # Funding Actions
    path('invest/<int:project_id>/', views.make_investment, name='make_investment'),
    path('pledge/<int:project_id>/', views.make_pledge, name='make_pledge'),
    
    # Investment Management
    path('projects/<int:project_id>/investments/', views.manage_investments, name='manage_investments'),
    path('investments/<int:investment_id>/<str:status>/', views.update_investment_status, name='update_investment_status'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    

]