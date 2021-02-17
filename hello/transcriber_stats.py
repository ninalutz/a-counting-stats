# Date
# ID
# Languages: List of languages (in order of transcription)
# Calls: List of call # per languages

from datetime import datetime, timedelta
import math
import os
import collections
import pytz
import zipcodes
import requests, json, csv
import os, io
import random as rand
import hashlib
from rq import Queue
from datetime import datetime
import pickle
import logging
import urllib

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


from .models import Call, Recording, Number, Language, Transcription, City, Participant, MergedAudio


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

def was_caller(participant, call):
	try:
		if call.participant == participant:
			return "y"
		return "n"
	except:
		return "n"

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

def get_trans_stats(start_date, end_date):
	out = {"users": []}
	transcribers = set()
	participants_added = set()
	participants_dict = {}
	#only get transcriptions from relevant dates
	transcribed_calls = Transcription.objects.filter(created_at__gt=start_date, created_at__lte=end_date, call__isnull=False).values('call').distinct()
	calls = [c['call'] for c in transcribed_calls]
	first_for_language = {}
	for c in calls:
		# t = Transcription.objects.filter(call=c)[0]
		participants_raw = Transcription.objects.filter(call=c).values('participant').distinct()
		participants_to_calc = [p['participant'] for p in participants_raw]
		for p in participants_to_calc:
			t = Transcription.objects.filter(call=c, participant=p)[0]
			if t.participant not in participants_added:
				user_dict = {"Updated on": get_user_date(t.participant, end_date), 
				"ID": get_hash(t.participant), "Call-Language" : {}, "Caller":was_caller(t.participant, t.call)}
				user_dict["Call-Language"][t.language.name] = 1
				participants_dict[get_hash(t.participant)] = user_dict
				participants_added.add(t.participant)
				if t.language.name not in first_for_language.keys():
					first_for_language[t.language.name] = (t.participant, t)
				else:
					if t.created_at < first_for_language[t.language.name][1].created_at:
						first_for_language[t.language.name] = (t.participant, t)
			else:
				user_dict = participants_dict[get_hash(t.participant)]
				if t.language.name in user_dict["Call-Language"].keys():
					user_dict["Call-Language"][t.language.name] += 1
				else:
					user_dict["Call-Language"][t.language.name] = 1
				if t.language.name not in first_for_language.keys():
					first_for_language[t.language.name] = (t.participant, t)
				else:
					if t.created_at < first_for_language[t.language.name][1].created_at:
						first_for_language[t.language.name] = (t.participant, t)
	for p in participants_dict.values():
		p["Languages"] = []
		p["Calls"] = []
		for language in p["Call-Language"].keys():
			p["Languages"].append(language)
			p["Calls"].append(p["Call-Language"][language])
			user_dict = {"Updated on": p["Updated on"], "ID":p["ID"], "Language": language,
			"Calls": p["Call-Language"][language]}

			if p["ID"] != "n/a":
				try:
					if p["ID"] == str(first_for_language[language][0].hash_id):
						user_dict["New"] = "y"
					else:
						user_dict["New"] = "n"
				except:
					user_dict["New"] = "n"
				user_dict["Caller"] = p["Caller"]
				out["users"].append(user_dict)
	out["users"] = sorted(out["users"], key=lambda k: k['Updated on'], reverse=True) 
	return out