from django.urls import path
from apps.projects import views

app_name = 'projects'

urlpatterns = [
    # Public views
    path('', views.home, name='home'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('about/', views.about_page, name='about_page'),

    # Project management (founders)
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('projects/<int:project_id>/add-reward/', views.add_reward, name='add_reward'),
    path('projects/<int:project_id>/add-update/', views.add_update, name='add_update'),

    # Donations
    path('projects/<int:project_id>/pledge/', views.make_pledge, name='make_pledge'),
    path('donation/callback/', views.donation_callback, name='donation_callback'),
    path('my-donations/', views.my_donations, name='my_donations'),

    # Investments
    path('projects/<int:project_id>/invest/', views.investment_proposal, name='investment_proposal'),
    path('my-investments/', views.my_investments, name='my_investments'),
]
