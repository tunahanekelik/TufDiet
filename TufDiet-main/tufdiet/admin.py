from django.contrib import admin
from .models import TufProfile, MealEntry


@admin.register(TufProfile)
class TufProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_status', 'is_verified', 'height', 'weight', 'created_at']
    list_filter = ['user_status', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ['food_name', 'user', 'calories', 'protein', 'carbs', 'fat', 'ai_confidence', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['food_name', 'user__username']
    readonly_fields = ['created_at']
