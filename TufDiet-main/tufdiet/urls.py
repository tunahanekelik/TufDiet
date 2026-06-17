from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TufProfileViewSet, MealEntryViewSet, WeightHistoryViewSet, DietPlanMealViewSet, health_check, ai_analyze
from knox import views as knox_views
from .auth_views import LoginAPI, RegisterAPI

router = DefaultRouter()
router.register(r'profiles', TufProfileViewSet, basename='profile')
router.register(r'meals', MealEntryViewSet, basename='meal')
router.register(r'weight-history', WeightHistoryViewSet, basename='weight-history')
router.register(r'diet-plans', DietPlanMealViewSet, basename='diet-plan')

urlpatterns = [
    path('', include(router.urls)),
    path('my-profile/', TufProfileViewSet.as_view({'get': 'my_profile'}), name='my-profile'),
    path('update-my-profile/', TufProfileViewSet.as_view({'patch': 'update_my_profile'}), name='update-my-profile'),
    path('upload-meal/', MealEntryViewSet.as_view({'post': 'upload_meal'}), name='upload-meal'),
    path('daily-summary/', MealEntryViewSet.as_view({'get': 'daily_summary'}), name='daily-summary'),
    path('weekly-summary/', MealEntryViewSet.as_view({'get': 'weekly_summary'}), name='weekly-summary'),
    path('health/', health_check, name='health-check'),
    path('ai-analyze/', ai_analyze, name='ai-analyze'),
    path('auth/login/', LoginAPI.as_view(), name='login'),
    path('auth/register/', RegisterAPI.as_view(), name='register'),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='logout'),
]
