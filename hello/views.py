from django.shortcuts import render
from datetime import datetime
import json
from .models import Greeting
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, Http404

from .hotline_stats import combo_stats, get_local_code, get_test_numbers, get_city_from_hotline
from .transcriber_stats_helper import get_trans_stats
from .language_stats import get_languages_over_time, get_specific_language_over_time
from .languages_stats import get_unknown_stats, new_languages_over_time, new_languages_over_time_agg


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


"""
This is a function that calls methods from the hotline_stats.py file
Gets statistics from hotline numbers about usage and exports to Google sheets
"""
@csrf_exempt
def stats(request, city, start_month, start_day, end_month, end_day):
    out = {}
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    if request.method == 'GET':
        out = combo_stats(city, start, end)
    return JsonResponse(out)


#Gets language stats over time from a city
@csrf_exempt
def languages_stats(request, city, start_month, start_day, end_month, end_day):
    try:
        print("Queue lengths: " + str(len(q.jobs)) + " " +  str(len(q2.jobs)) + " " +  str(len(q3.jobs)))
    except:
        print("Error printing queue length")
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    out = get_languages_over_time(city, start, end)
    return JsonResponse(out)

@csrf_exempt
def new_languages_stats(request, start_month, start_day, end_month, end_day):
    try:
        print("Queue lengths: " + str(len(q.jobs)) + " " +  str(len(q2.jobs)) + " " +  str(len(q3.jobs)))
    except:
        print("Error printing queue length")
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    out = new_languages_over_time(start, end)
    return JsonResponse(out)

@csrf_exempt
def new_languages_agg(request, start_month, start_day, end_month, end_day, delta):
    try:
        print("Queue lengths: " + str(len(q.jobs)) + " " +  str(len(q2.jobs)) + " " +  str(len(q3.jobs)))
    except:
        print("Error printing queue length")
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    out = new_languages_over_time_agg(start, end, delta)
    return JsonResponse(out)

#specific language stats
@csrf_exempt
def specific_language_stats(request, language, start_month, start_day, end_month, end_day):
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    out = get_specific_language_over_time(language, start, end)
    return JsonResponse(out)

@csrf_exempt
def transcriber_stats(request, start_month, start_day, end_month, end_day):
    out = {}
    start = datetime(2020, int(start_month), int(start_day), 0, 0, 0)
    end = datetime(2020, int(end_month), int(end_day), 0, 0, 0)
    if request.method == 'GET':
        out = get_trans_stats(start, end)
    return JsonResponse(out)