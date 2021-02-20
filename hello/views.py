from django.shortcuts import render
from datetime import datetime
import json
from .models import Greeting
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, Http404

from .hotline_stats import combo_stats, get_local_code, get_test_numbers, get_city_from_hotline
from .transcriber_stats import get_trans_stats
from .language_stats import get_languages_over_time, get_specific_language_over_time, get_untranscribed_languages
from .language_stats import get_unknown_stats, new_languages_over_time, new_languages_over_time_agg


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")

"""
Returns JSON output of languages without transcriptions
Untranscribed langauges sheet
"""
@csrf_exempt
def untranscribed_languages(request):
    out = {"languages":get_untranscribed_languages()}
    return JsonResponse(out)

"""
This is a function that calls methods from the hotline_stats.py file
Gets statistics from hotline numbers about usage and exports to Google sheets

TODO: Add a year parameter //added 2/20/21
Test links: *will change*
"""
@csrf_exempt
def stats(request, city, start_year, start_month, start_day, end_year, end_month, end_day):
    out = {}
    start = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0)
    end = datetime(int(end_year), int(end_month), int(end_day), 0, 0, 0)
    if request.method == 'GET':
        out = combo_stats(city, start, end)
    return JsonResponse(out)


"""
Gets language stats over time from a city -- New transcripts by month sheet
TODO: Add a year parameter //added 2/20/21
"""
@csrf_exempt
def languages_stats(request, city, start_year, start_month, start_day, end_year, end_month, end_day):
    start = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0)
    end = datetime(int(end_year), int(end_month), int(end_day), 0, 0, 0)
    out = get_languages_over_time(city, start, end)
    return JsonResponse(out)


"""
Tells us languages that were added in a date range -- New languages sheet
TODDO: Add a year parameter //added 2/20/21
"""
@csrf_exempt
def new_languages_stats(request, start_year, start_month, start_day, end_year, end_month, end_day):
    start = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0)
    end = datetime(int(end_year), int(end_month), int(end_day), 0, 0, 0)
    out = new_languages_over_time(start, end)
    return JsonResponse(out)

"""
Returns transcriber stats for "New transcripts" sheet
TODO: Add year param //added 2/20/21
"""
@csrf_exempt
def transcriber_stats(request, start_year, start_month, start_day, end_year, end_month, end_day):
    out = {}
    start = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0)
    end = datetime(int(end_year), int(end_month), int(end_day), 0, 0, 0)
    if request.method == 'GET':
        out = get_trans_stats(start, end)
    return JsonResponse(out)
