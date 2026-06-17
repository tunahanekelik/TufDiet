code_to_append = """    weight_history = []
    if has_profile:
        try:
            from .models import WeightHistory
            weight_history = list(WeightHistory.objects.filter(
                user=request.user
            ).order_by('-recorded_at')[:30])
        except:
            pass
    
    today = timezone.now().date()
    daily_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        summary = get_daily_summary(request.user, date)
        
        status = None
        if has_profile and profile.target_calories:
            progress = get_nutrition_status_progress(
                summary['total_calories'],
                profile.target_calories
            )
            status = progress
        
        summary['status'] = status
        summary['display_date'] = date.strftime('%d %b') if i == 0 else date.strftime('%a')
        daily_data.append(summary)
        summary['date_str'] = date.strftime('%Y-%m-%d')
        
    if profile and has_profile and profile.target_calories:
        progress = round((sum(d['total_calories'] for d in daily_data) / profile.target_calories) * 100)
    else:
        progress = 0
    
    # Get dynamic advice
    advice_list = []
    if has_profile and profile.goal:
        from tufdiet.health_calculator import get_general_advice
        advice_list = get_general_advice(profile.goal, profile.activity_level)

    # --- GETTING HISTORY DATA ---
    # generating the weekly and monthly summaries rn
    weekly_summary = {
        'total_calories': sum(d['total_calories'] for d in daily_data),
        'total_protein': sum(d['total_protein'] for d in daily_data),
        'total_carbs': sum(d['total_carbs'] for d in daily_data),
        'total_fat': sum(d['total_fat'] for d in daily_data),
        'days_tracked': sum(1 for d in daily_data if d['meal_count'] > 0),
    }
    
    monthly_data = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        monthly_data.append(get_daily_summary(request.user, date))
        
    monthly_summary = {
        'total_calories': sum(d['total_calories'] for d in monthly_data),
        'total_protein': sum(d['total_protein'] for d in monthly_data),
        'total_carbs': sum(d['total_carbs'] for d in monthly_data),
        'total_fat': sum(d['total_fat'] for d in monthly_data),
        'days_tracked': sum(1 for d in monthly_data if d['meal_count'] > 0),
    }
    
    context = {
        'profile': profile,
        'has_profile': has_profile,
        'goals': GOAL_DISPLAY_NAMES,
        'activity_levels': ACTIVITY_DISPLAY_NAMES,
        'weight_history': weight_history,
        'daily_data': daily_data,
        'weekly_summary': weekly_summary,
        'monthly_summary': monthly_summary,
        'progress': progress,
        'advice_list': advice_list,
    }
    return render(request, 'health_profile.html', context)


# --- ADDING WEB DIET PLAN ---
# creating the new view for the django web app diet plan rn
@login_required
def diet_plan(request):
    from django.utils import timezone
    from .models import DietPlanMeal
    
    today = timezone.now().date()
    # getting today's plan and sorting by time so it looks chronological
    plan_meals = DietPlanMeal.objects.filter(user=request.user, date=today).order_by('suggested_time')
    
    try:
        profile = request.user.tuf_profile
        has_profile = all([profile.height, profile.weight, profile.age, profile.gender])
    except:
        profile = None
        has_profile = False
        
    context = {
        'meals': plan_meals,
        'has_profile': has_profile,
        'profile': profile
    }
    return render(request, 'diet_plan.html', context)


@login_required
def add_water(request):
    if request.method == 'POST':
        try:
            profile = request.user.tuf_profile
            profile.water_consumed += 1
            profile.save()
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'water_consumed': profile.water_consumed,
                'water_target': profile.water_target,
                'progress': round((profile.water_consumed / profile.water_target) * 100)
            })
        except:
            from django.http import JsonResponse
            return JsonResponse({'success': False})
    from django.http import JsonResponse
    return JsonResponse({'success': False})


@login_required
def delete_weight(request, record_id):
    if request.method == 'POST':
        from .models import WeightHistory
        try:
            record = WeightHistory.objects.get(id=record_id, user=request.user)
            record.delete()
            profile = request.user.tuf_profile
            latest = WeightHistory.objects.filter(user=request.user).order_by('-recorded_at').first()
            if latest:
                profile.weight = latest.weight
            profile.save()
            from django.contrib import messages
            messages.success(request, 'Weight entry deleted.')
        except WeightHistory.DoesNotExist:
            from django.contrib import messages
            messages.error(request, 'Record not found.')
        from django.shortcuts import redirect
        return redirect('health-profile')
    from django.shortcuts import redirect
    return redirect('health-profile')
"""

with open('tufdiet/web_views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('tufdiet/web_views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines[:466])
    f.write(code_to_append)

print('Successfully restored web_views.py')
