# Date
# ID
# Languages: List of languages (in order of transcription)
# Calls: List of call # per languages

from datetime import datetime, timedelta
import math
import calendar
import os
import collections
import pytz
import zipcodes
import requests, json, csv
import os, io
import random as rand
import hashlib
from datetime import datetime
import logging
import urllib
from django.core.files.storage import default_storage
from django.core.files import File
from django.core.files.base import ContentFile
from django.db.models import Count, F, Q

#DJango imports
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from django.http import HttpResponseRedirect, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from django.db.models import Q
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from collections import OrderedDict 

from .models import Call, Recording, Number, Language, Transcription, City, Participant, MergedAudio

env = os.getenv('ENVIRONMENT', default='dev')


"""
Returns list of names of languages with no transcriptions
"""
def get_untranscribed_languages():
	language_list = []
	languages = list(Language.objects.all().order_by('name'))

	for l in languages:
		raw_trans = list(Transcription.objects.filter(language=l))
		if not raw_trans or len(raw_trans) == 0:
			language_list.append(l.name)
	return language_list.sort()

def get_user_date(participant, end_date):
	try:
		if participant: 
			return participant.updated_at.replace(tzinfo=None).strftime("%m/%d/%Y")
	except:
		return end_date.strftime("%m/%d/%Y")

def get_hash(participant):
	try:
		if participant: 
			return str(participant.hash_id)
	except:
		return "n/a"
	return "n/a"

def get_hash(participant):
	try:
		if participant: 
			return str(participant.hash_id)
	except:
		return "n/a"
	return "n/a"

def was_caller(participant, call):
	if call.participant == participant:
		return "y"
	return "n"

def get_call_date(call):
	return call.ended_at.strftime("%m/%d/%y")


def stringify_list(list_to_convert):
	if len(list_to_convert) > 1:
		list_to_convert.sort()
		out_string = ""
		for l in range(len(list_to_convert)):
			out_string += str(list_to_convert[l])
			if l != len(list_to_convert) - 1:
				out_string += ", "
		return out_string
	return str(list_to_convert[0])


"""
Goal: Get specific language over time 
Test URL: spec_language/English/7/1/7/15
"""
def get_specific_language_over_time(language_name, start_date, end_date):
	out = {"dates": []}
	try:
		language = Language.objects.filter(name=language_name)[0]
		delta = end_date - start_date	  # as timedelta
		days_to_check = []
		for i in range(delta.days + 1):
			day = start_date + timedelta(days=i)
			days_to_check.append(day)

		for d in days_to_check:
			l_dict = OrderedDict()
			trans_calls_set = Transcription.objects.filter(language=language, created_at__gt=start_date, created_at__lte=d, call__isnull=False).values('call').distinct()
			l_dict["Date"] = str(d.strftime("%m/%d/%Y"))
			l_dict["Calls"] = str(len(trans_calls_set))
			out["dates"].append(l_dict)
	except Exception as e:
		print(e)
		out = {"Invalid language name": language_name}
	return out 

"""
Goal:
Datastructure that shows a timeseries of the langauge transcriptions
For each language, get the number of transcriptions cummulative on that date

Test URL: languages_stats/us/1/1/7/7
"""
def get_languages_over_time(city, start_date, end_date):
	# try:
	# 	fill_unknown_archives()
	# except Exception as e:
	# 	print(e)
	out = {"languages": []}
	languages = list(Language.objects.all().order_by('name'))

	delta = end_date - start_date	  # as timedelta
	days_to_check = []
	months_to_check = []
	date_ranges_to_check = []

	#get the days and months between start and end 
	for i in range(delta.days + 1):
		day = start_date + timedelta(days=i)
		if day.month not in months_to_check:
			months_to_check.append(day.month)
		days_to_check.append(day)

	for month in months_to_check:
		first_of_month = datetime(2020, int(month), 1, 0, 0, 0)
		last_of_month = datetime(2020, int(month), calendar.monthrange(2020, month)[1], 0, 0, 0)
		date_ranges_to_check.append((first_of_month, last_of_month))

	languages_to_process = []

	for l in languages:
		raw_trans = list(Transcription.objects.filter(language=l, created_at__gte=start_date, created_at__lte=end_date))
		if not raw_trans or len(raw_trans) == 0:
			languages.remove(l)
		else:
			languages_to_process.append(l)		

	languages_to_process.append(Language.objects.filter(name='English')[0])

	total_transcribed = 0

	for l in languages_to_process:
		l_dict = OrderedDict()
		for d in date_ranges_to_check:
			l_dict["Language"] = l.name
			trans_calls_set = Transcription.objects.filter(language=l, created_at__gt=start_date, created_at__lte=d[1]).values('call').distinct()
			l_dict[d[0].strftime("%B")] = len(trans_calls_set)
		if l.name != "Unknown":
			out["languages"].append(l_dict)

	# for l_dict in out["languages"]:
	last_month = date_ranges_to_check[len(date_ranges_to_check)-1][0].strftime("%B")
	out["languages"] = sorted(out["languages"], key=lambda k: k[last_month], reverse=True) 

	other_dict = {}
	other_dict["Language"] = "Other"
	for d in date_ranges_to_check:
		other_dict[d[0].strftime("%B")] = 0
		for i in range(10, len(out["languages"])):
			other_dict[d[0].strftime("%B")]+= out["languages"][i][d[0].strftime("%B")]

	final_out = {"languages":[]}
	final_set = []
	final_set = out["languages"][0:10]
	final_set.append(other_dict)
	#print(final_set)
	final_out["languages"] = sorted(final_set, key=lambda k: k[last_month],reverse=True)
	return final_out

"""
Aggregate amounts of new languages on the daily basis 
Only for languages where it is the first time they were transcribed 

Test link: new_languages/7/1/8/1

Day by day: 
{Transcribe date: "", Recorded on: "", ID: "", Caller "y/n", Language: ""}
"""
def new_languages_over_time(start_date, end_date):
	out = {"dates": []}
	delta = end_date - start_date	  # as timedelta
	days_to_check = []
	languages_added = set()
	l_dict = OrderedDict()
	trans_calls = Transcription.objects.filter(created_at__gt=start_date, created_at__lte=end_date, call__isnull=False).values('call').distinct()
	calls_to_process = [c['call'] for c in trans_calls]
	for c in calls_to_process:
		transcribe = Transcription.objects.filter(call=c)[0]
		if transcribe:
			candidate_language = transcribe.language
			if candidate_language.name not in languages_added:
				earliest_transcribe = Transcription.objects.filter(language=candidate_language, call__isnull=False).order_by('created_at')[0]
				call_obj = earliest_transcribe.call
				transcriber = earliest_transcribe.participant
				languages_added.add(candidate_language.name)
				l_dict = {"Recorded on": call_obj.ended_at.strftime("%m/%d/%Y"),
				"Transcribed on": earliest_transcribe.created_at.strftime("%m/%d/%Y"), 
				"Caller": was_caller(transcriber, call_obj),
				"Language": candidate_language.name
				}
				languages_added.add(candidate_language.name)
				out["dates"].append(l_dict)
	out["dates"] = sorted(out["dates"], key=lambda k: k['Transcribed on'], reverse=True) 
	return out

"""
Aggregate amounts of new languages on the daily basis 
Only for languages where it is the first time they were transcribed 

Test link: new_languages/7/1/8/1

Day by day: 
{Transcribe date: "", Recorded on: "", ID: "", Caller "y/n", Language: ""}
"""
def new_languages_over_time_agg(start_date, end_date, delta):
	month_strings = {1: "January", 2: "February", 3: "March", 4: "April",
	5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 
	11: "November", 12: "December"}
	out = {"dates": []}
	date_delta = end_date - start_date	  # as timedelta
	days_to_check = []
	languages_added = set()
	months_to_check = []
	l_dict = OrderedDict()
	trans_calls = Transcription.objects.filter(created_at__gt=start_date, created_at__lte=end_date, call__isnull=False).values('call').distinct()
	calls_to_process = [c['call'] for c in trans_calls]
	for c in calls_to_process:
		transcribe = Transcription.objects.filter(call=c)[0]
		if transcribe:
			candidate_language = transcribe.language
			if candidate_language.name not in languages_added:
				earliest_transcribe = Transcription.objects.filter(language=candidate_language, call__isnull=False).order_by('created_at')[0]
				call_obj = earliest_transcribe.call
				transcriber = earliest_transcribe.participant
				languages_added.add(candidate_language.name)
				l_dict = {"Recorded on": call_obj.ended_at.strftime("%m/%d/%Y"),
				"Transcribed on": earliest_transcribe.created_at.strftime("%m/%d/%Y"),  
				"Caller": was_caller(transcriber, call_obj),
				"Language": candidate_language.name
				}
				languages_added.add(candidate_language.name)
				out["dates"].append(l_dict)
	print(delta)
	if delta == 'month':
		new_out = {"months": []}
		l_dict = {}
		#get the months between start and end 
		for i in range(date_delta.days + 1):
			day = start_date + timedelta(days=i)
			if day.month not in months_to_check:
				months_to_check.append(day.month)
		for m in months_to_check:
			l_dict[m] = 0
		for d in out["dates"]:
			try:
				l_dict[int(d["Transcribed on"].split("/")[0])] += 1
				#print(int(d["Transcribed on"].split("/")[0]))
			except:
				print("Dictionary error")
		print(l_dict)
		for m in l_dict.keys():
			new_out["months"].append({"Month":month_strings[m], "Transcriptions": str(l_dict[m])})
		out = new_out
	if delta == 'week':
		new_out = {"weeks": []}
		l_dict = {}
		weeks_to_check = []
		#get the weeks between start and end 
		for i in range(date_delta.days + 1):
			day = start_date + timedelta(days=i)
			if day.day % 7 == 0:
				weeks_to_check.append(day)
				l_dict[day] = 0
		for d in out["dates"]:
			t_month = int(d["Transcribed on"].split("/")[0])
			t_day = int(d["Transcribed on"].split("/")[1])
			t_year = int(d["Transcribed on"].split("/")[2])
			t_date = datetime(t_year, t_month, t_day)
			print(t_date)
			for week_date in weeks_to_check:
				if t_date > start_date and t_date <= week_date:
					l_dict[week_date] += 1
		for w in l_dict.keys():
			new_out["weeks"].append({"Week" : w.strftime("%m/%d/%Y"), "Transcriptions": str(l_dict[w])})
		out = new_out
	return out


"""
Goal: See time trends for how people transcribe the langauge recordings

Updates a running JSON 

Language transcribed
Transcribed on
Date the call was made
Was the transcriber the caller (y/n)
Participant 
"""
def get_unknown_stats(call, language, date, participant):
	print("Starting unknown")
	out = {}
	user_dict = OrderedDict()
	user_dict = {"Recorded on": get_call_date(call),
	"Transcribed on": date.strftime("%m/%d/%Y"), 
	"Call ID": call.hash_id, 
	"Caller": was_caller(participant, call), 
	"Language transcribed": language}
	try:
		out = load_json("unknown_languages.json")
		out["languages"].append(user_dict)
		print("Added to old JSON")
		out["languages"] = sorted(out["languages"], key=lambda k: k["Transcribed on"], reverse=True) 
		save_json("unknown_languages", out)
	except Exception as e:
		print("ERROR WITH UNKNOWN JSON")
		print(e)
		out = {"languages": []}
		out["languages"].append(user_dict)
		save_json("unknown_languages", out)
	print("ending unknown")

def save_json(filename, out):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Starting " + str(filename) + " at" + start_time)
    json_str = json.dumps(out)
    default_storage.delete(filename + '.json')
    aws_path = default_storage.save(filename + '.json', ContentFile(json_str.encode()))
    print('aws_path', aws_path)
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("Ending " + str(filename) + " at" + end_time)
    return aws_path

def load_json(aws_path):
    file = default_storage.open(aws_path).read()
    output = json.loads(file)
    return output
