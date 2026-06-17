"""
TufDiet AI Bot Views
chat_response and progress analytics endpoints
"""

import json
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST

from tufdiet.models import MealEntry, TufProfile
from .services import TufDietAI

# Singleton AI service
ai_engine = TufDietAI()

from django.views.decorators.csrf import csrf_exempt
from knox.auth import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

@csrf_exempt
@require_POST
def chat_response(request):
    """
    Authenticated POST-only view.
    Receives user message, processes through RAG-augmented LLM,
    returns clean JSON response.
    """
    user = request.user
    if not user.is_authenticated:
        try:
            auth_tuple = TokenAuthentication().authenticate(request)
            if auth_tuple is not None:
                user = auth_tuple[0]
                request.user = user
        except AuthenticationFailed:
            pass

    if not user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        question = data.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        question = request.POST.get('message', '').strip()

    if not question:
        return JsonResponse({
            'status': 'error',
            'response': 'Please provide a message.'
        }, status=400)

    # Extract user profile
    try:
        profile = request.user.tuf_profile
        user_data = {
            'weight': profile.weight or 70,
            'height': profile.height or 170,
            'target_calories': profile.target_calories or 2000,
            'goal': profile.goal or 'MAINTAIN_FAT_LOSS',
        }
    except TufProfile.DoesNotExist:
        user_data = {
            'weight': 70,
            'height': 170,
            'target_calories': 2000,
            'goal': 'MAINTAIN_FAT_LOSS',
        }

    answer = ai_engine.chat(user_data, question)

    return JsonResponse({
        'status': 'success',
        'response': answer,
    })


@login_required
def get_progress_data(request, period='weekly'):
    """
    Analytics view that aggregates meal data.
    Returns daily, weekly, or monthly totals.
    """
    today = timezone.now().date()

    if period == 'daily':
        days = 1
    elif period == 'weekly':
        days = 7
    elif period == 'monthly':
        days = 30
    else:
        days = 7

    start_date = today - timedelta(days=days - 1)
    start_dt = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )

    meals = MealEntry.objects.filter(
        user=request.user,
        created_at__gte=start_dt
    ).order_by('created_at')

    daily_totals = {}
    for meal in meals:
        day_key = meal.created_at.strftime('%Y-%m-%d')
        if day_key not in daily_totals:
            daily_totals[day_key] = {
                'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meals': 0
            }
        daily_totals[day_key]['calories'] += meal.calories
        daily_totals[day_key]['protein'] += meal.protein
        daily_totals[day_key]['carbs'] += meal.carbs
        daily_totals[day_key]['fat'] += meal.fat
        daily_totals[day_key]['meals'] += 1

    # Build series with zero-fill
    series = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        key = day.strftime('%Y-%m-%d')
        entry = daily_totals.get(key, {
            'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meals': 0
        })
        entry['date'] = key
        entry['day_name'] = day.strftime('%A')
        entry['short_date'] = day.strftime('%d %b')
        series.append(entry)

    totals = {
        'calories': sum(e['calories'] for e in series),
        'protein': sum(e['protein'] for e in series),
        'carbs': sum(e['carbs'] for e in series),
        'fat': sum(e['fat'] for e in series),
        'meals': sum(e['meals'] for e in series),
        'days_tracked': sum(1 for e in series if e['meals'] > 0),
    }

    return JsonResponse({
        'status': 'success',
        'period': period,
        'days': days,
        'series': series,
        'totals': totals,
    })


@login_required
def chat_hub_view(request):
    """
    Full-screen AI consultant chat page with profile sidebar.
    """
    try:
        profile = request.user.tuf_profile
    except TufProfile.DoesNotExist:
        profile = None

    return render(request, 'chat_hub.html', {
        'profile': profile,
    })
