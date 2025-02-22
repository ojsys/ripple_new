from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),

    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    
    # Edit URLs
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('projects/<int:pk>/edit/', views.edit_project, name='edit_project'),

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
    path('my-investments/', views.MyInvestmentsView.as_view(), name='my_investments'),
    path('investment/<int:pk>/', views.InvestmentDetailView.as_view(), name='investment_detail'),
    path('investment/<int:investment_id>/activate/', views.activate_investment, name='activate_investment'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),


]
# Add this at the end
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)