from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TufProfile


@receiver(post_save, sender=TufProfile)
def recalculate_macros_on_save(sender, instance, created, **kwargs):
    """
    Automatically recalculate BMR, TDEE and macro targets when profile is updated.
    """
    if not all([instance.height, instance.weight, instance.age, instance.gender]):
        return

    if hasattr(instance, '_recalculating'):
        return

    from .health_calculator import calculate_health_profile

    health_data = calculate_health_profile(instance)
    if health_data:
        instance.bmr = health_data.get('bmr')
        instance.tdee = health_data.get('tdee')
        instance.target_calories = health_data.get('target_calories')
        instance.target_protein = health_data.get('target_protein')
        instance.target_carbs = health_data.get('target_carbs')
        instance.target_fat = health_data.get('target_fat')
        instance._recalculating = True
        instance.save(update_fields=[
            'bmr', 'tdee', 'target_calories',
            'target_protein', 'target_carbs', 'target_fat', 'updated_at'
        ])
        del instance._recalculating


@receiver(post_save, sender=TufProfile)
def reset_water_daily(sender, instance, created, **kwargs):
    """
    Reset water consumed counter at midnight.
    """
    if hasattr(instance, '_recalculating'):
        return

    if instance.last_water_reset:
        if instance.last_water_reset.date() < timezone.now().date():
            instance.water_consumed = 0
            instance.last_water_reset = timezone.now()
            instance._recalculating = True
            instance.save(update_fields=['water_consumed', 'last_water_reset'])
            del instance._recalculating
    else:
        instance.last_water_reset = timezone.now()
        instance._recalculating = True
        instance.save(update_fields=['last_water_reset'])
        del instance._recalculating