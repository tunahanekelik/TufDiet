from django.urls import path
from django.shortcuts import redirect
from . import web_views
from . import views

def accounts_login_redirect(request):
    return redirect('login')

urlpatterns = [
    path('', web_views.home, name='home'),
    path('login/', web_views.user_login, name='login'),
    path('register/', web_views.user_register, name='register'),
    path('logout/', web_views.user_logout, name='logout'),
    path('dashboard/', web_views.dashboard, name='dashboard'),
    path('add-meal/', web_views.add_meal, name='add-meal'),
    path('get-nutrition/', web_views.get_nutrition, name='get-nutrition'),
    path('profile/', web_views.health_profile, name='health-profile'),
    # --- ADDING WEB DIET PLAN URL ---
    # replaced the old progress url with diet-plan rn
    path('diet-plan/', web_views.diet_plan, name='diet-plan'),
    path('add-water/', web_views.add_water, name='add-water'),
    path('delete-weight/<int:record_id>/', web_views.delete_weight, name='delete-weight'),
    path('dev-panel/', views.developer_dashboard, name='dev_dashboard'),
    
    # Accounts login redirect
    path('accounts/login/', accounts_login_redirect, name='accounts_login'),
]
