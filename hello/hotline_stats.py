from twilio.rest import Client
from datetime import datetime, timedelta
import requests
import math
import os
import collections
import pytz
import zipcodes

from .models import Call, Recording, Number, Language, Transcription, City, Participant, MergedAudio

#Twilio Imports
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_api_header = 'https://%s:%s@api.twilio.com' % (account_sid, auth_token)

client = Client(account_sid, auth_token)

NYC_hotline = '+19179056647'
Boston_hotline = '+18576630688'
Chicago_hotline = '+17732324266'
LA_hotline = '+13237666762'
Miami_hotline = '+17867566233'
test_num = '+19292096703'
US_hotline = '+18449593197'
Omaha_hotline = '+14022512426'
Houston_hotline = '+12812488730'


city_hotlines = { NYC_hotline: "New York City", Chicago_hotline: "Chicago",
Boston_hotline: "Boston",  LA_hotline:"LA",  Miami_hotline: "Miami",
 US_hotline: "US", Houston_hotline:"Houston", Omaha_hotline: "Omaha"}

def get_city_from_hotline(number):
	if number in city_hotlines:
		return city_hotlines[number]
	return "N/A"


florida_codes = ['305', '786', '754', '954', 
'772', '321', '407', '386', '727', '813',
'941', '239', '863','561','352','904']

tristate_codes = ['201', '203', '212', '272', 
'289', '315',  '332', '332', '343', '347', 
'365', '413', '416', '437', '450', '475', '516', 
'518', '551', '570', '579', '585', '607', 
'613',  '631', '646', '647', '680', 
'689', '716', '718', '802', '814', '819', '838', 
'845', '860', '862', '873', '905', '914', 
'917', '929', '934', '959', '973']

mass_codes = ['617','857','413','339','351','508',
'774','781','978']

illinois_codes = ['217','309', '312', '331', '630',
'618','708','773','779','815','847','224','872']

la_codes = ['209', '213', '279', '310', '323', 
'424', '442', '442', '530',  '559', '562', 
'619', '626', '657', '661', '707', '714', '747', 
'760', '805', '818', '820', '831', '840', 
'840', '858', '909', '916', '949', '951']

omaha_codes = ['402', '531']

houston_codes = ['281', '346', '713', '832']

code_cities = {"nyc": tristate_codes, "bos": mass_codes, "la": la_codes, 
"chi": illinois_codes, "mia": florida_codes, "us": [], "hou": houston_codes,
"oma": omaha_codes}

test_numbers = ['+14802859998', '+16179227758', 
'+16178703506', '+16176450327'] #personal numbers

hotline_cities = { "nyc": NYC_hotline, "bos" : Boston_hotline, "mia": Miami_hotline, 
"la": LA_hotline, "chi": Chicago_hotline, "hou": Houston_hotline, "us": US_hotline,
"oma": Omaha_hotline}

def get_test_numbers():
	return test_numbers

def get_local_code(city, code):
	local_codes = code_cities[city]
	if len(local_codes) > 0:
		if code in local_codes:
			return "yes"
		else:
			return "no"
	return "n/a"

def get_untranscribed_calls(hash_id):
	p = list(Participant.objects.filter(hash_id = hash_id))[0]
	calls = list(Call.objects.filter(participant=p))
	total_transcriptions = 0
	for c in calls:
		transcriptions = list(Transcription.objects.filter(call=c))
		if len(transcriptions) > 0:
			total_transcriptions += 1
	return len(calls) - total_transcriptions

#Utility function 
def mainmenu_messages(messages, user_dict):
	for m in messages:
		if m.body.lower()== "transcribe":
			user_dict["TRANSCRIBE"] +=1
		if m.body.lower() ==  "credit":
			user_dict["CREDIT"] += 1
		if m.body.lower() == "stop":
			user_dict["STOP"] += 1
		if m.body == '1':
			user_dict["Record"] += 1
		if m.body == '2':
			user_dict["Transcribe"] +=1
		if m.body == '3':
			user_dict["Listen"] +=1
		if m.body == '4':
			user_dict["Watch"] +=1
		if m.body == '5':
			user_dict["Subscribe"] +=1
		if m.body.lower() == "help":
			user_dict["HELP"] +=1 

def duration_stamp(val):
	sec =  timedelta(seconds=int(val))
	d = datetime(1,1,1) + sec
	stamp = d.strftime("%H:%M:%S")
	return stamp

def make_strings(a_dict):
	for key, value in a_dict.items():
		key = str(key)
		a_dict[key] = str(value)

def processing_status(messages, user_dict):
	for m in messages:
		if 'we’re very sorry but something went wrong' in m.body:
			user_dict["Misprocessed"] += 1

def get_hash(num):
	try:
		participant = list(Participant.objects.filter(phone_number = num))[0]
		if participant: 
			return participant.hash_id
	except:
		return "n/a"
	return "n/a"


def get_zipcode(num):
	try:
		participant = list(Participant.objects.filter(phone_number = num))[0]
		if participant: 
			if participant.zipcode == '':
				return '00000'
			return participant.zipcode
	except:
		return "n/a"
	return "n/a"

def get_city_from_zipcode_copy(zipcode, to_number):
     if not zipcode:
         return get_city_from_hotline(to_number)
     city_names = [z['city'] for z in zipcodes.matching(zipcode)]
     if city_names:
         return city_names[0].upper()[0:2]
     return get_city_from_hotline(to_number)

# def get_city(num):
# 	try:
# 		participant = list(Participant.objects.filter(phone_number = num))[0]
# 		call = list(Call.objects.filter(from_number=num))[0]
# 		to_number = ""
# 		if call:
# 			to_number = call.to_number
# 		if participant: 
# 			return str(get_city_from_zipcode_copy(participant.zipcode,to_number))
# 	except:
# 		return "n/a"
# 	return "n/a"

def get_city(num):
	try:
		participant = list(Participant.objects.filter(phone_number = num))[0]
		if participant: 
			return str(participant.city.code).upper()
	except:
		return "n/a"
	return "n/a"

def get_reminders(num):
	out_messages = client.messages.list(to=num)
	reminders = 0
	for m in out_messages:
		if "Hello from A Counting, your call(s) still haven't been reviewed" in m.body:
			reminders+= 1
	return reminders

def get_success(total_reminders, num, untranscribed_calls):
	if total_reminders > 0 and untranscribed_calls == 0:
		return "y"
	if total_reminders > 0 and untranscribed_calls > 0:
		return "n"
	return "n/a"

def get_caller_date(num, user_calls):
	try:
		participant = list(Participant.objects.filter(phone_number = num))[0]
		if participant: 
			return participant.updated_at.replace(tzinfo=None)
	except:
		dates = []
		for c in user_calls:
			dates.append(c.date_created)
		dates.sort()
		return dates[0].replace(tzinfo=None)
	return ""

def get_user_date(user_messages, user_calls, start_date, end_date, num):
	try:
		participant = list(Participant.objects.filter(phone_number = num))[0]
		if participant: 
			return participant.updated_at.replace(tzinfo=None).strftime("%m/%d/%Y")
	except:
		return end_date.strftime("%m/%d/%Y")

def combo_stats(city, start_date, end_date):
	non_participants = 0
	# if environment != 'prod':
	# 	print(f'Hotline_stats aborted in env={environment}')
	# 	return
	out = {"users": []}
	hotline = hotline_cities[city]
	local_codes = code_cities[city]
	messages = client.messages.list(
							   date_sent_after=start_date,
							   date_sent_before=end_date,
							   to=hotline
						   )
	calls = client.calls.list(to=hotline, 
		start_time_before=end_date, 
		start_time_after=start_date)

	#get all the users for sms and calls
	sms_users = set()
	call_users = set()

	#get messages first -- faster pull req
	for m in messages:
		user_num = m.from_
		if user_num not in test_numbers:
			sms_users.add(m.from_)

	#get users who are not in sms -- people who have *only* called
	for c in calls:
		if c.from_ not in sms_users and c.from_ not in test_numbers:
			call_users.add(c.from_)

	#make user dicts for sms users 
	for num in sms_users:
		user_dict = collections.OrderedDict()
		user_dict = collections.OrderedDict({"Date": "", 
		"ID": "", "Zip code":  get_zipcode(num), "City": get_city(num),
		"Total calls": 0, "Total texts": 0,"First contacted": "text",
		"Participated": 0, "Listened": 0,  "Uncompleted": 0, 
		"Untranscribed": 0, "Misprocessed": 0, 
		"Record": 0, "Transcribe": 0, "Listen": 0, "Watch": 0,
		"Subscribe": 0, "STOP": 0, "HELP": 0, "TRANSCRIBE": 0, "CREDIT": 0,
		"Total sent": get_reminders(num), "Received": "n/a", "Success": "n/a"})
		user_messages = client.messages.list(to=hotline, from_ = num)
		user_calls = client.calls.list(to=hotline, from_ = num)
		out_going_messages = list(client.messages.list(to=num, from_ = hotline))
		#print("outgoing: " + str(len(out_going_messages)) + str(type(out_going_messages)))
		user_dict["Total calls"] = str(len(user_calls))
		user_dict["Total texts"] = str(len(user_messages))
		user_dict["Date"] = get_user_date(user_messages, user_calls, start_date, end_date, num)

		user_dict["ID"] = get_hash(num)
		if user_dict["ID"] != "n/a":
			try:
				user_dict["Untranscribed"] = get_untranscribed_calls(user_dict["ID"])
			except Exception as e:
				print(e)
				
		processing_status(out_going_messages, user_dict)
		mainmenu_messages(user_messages, user_dict)

		if user_dict["Total sent"] >= 1:
			user_dict["Received"] = "y"

		if user_dict["Total sent"] < 1 and user_dict["Untranscribed"] > 0:
			now_date = datetime.now()
			now_simplified = datetime(now_date.year, now_date.month, now_date.day)
			if get_caller_date(num, user_calls) != "":
				diff = now_simplified - get_caller_date(num, user_calls)
				if diff.days >= 7:
					user_dict["Received"] = "n"

		if user_dict["Total sent"] == 0:
			user_dict["Received"] = "n/a"

		for c in user_calls:
			if c.end_time <= user_messages[0].date_sent:
				user_dict["First contacted"] = "call"
				break
			if c.end_time > user_messages[0].date_sent:
				user_dict["First contacted"] = "text"
				break

		if len(user_calls) == 0:
			user_dict["First contacted"] = "text"

	
		user_dict["Success"] = get_success(user_dict["Total sent"], num, user_dict["Untranscribed"])

		#print("Num calls: " + str(len(list(Call.objects.filter(city__code=city, from_number = num)))))
		#Add completed calls status 
		for call in Call.objects.filter(city__code=city, from_number = num):
			recordings = Recording.objects.filter(call__id=call.id)
			n = len(recordings)
			#print("Number recordings: " + str(n))
			if n == 0:
				user_dict["Listened"] += 1
			if n < 6 and n >= 1:
				user_dict["Uncompleted"] += 1 
				user_dict["Participated"] += 1
			if n >=6:
				user_dict["Participated"] += 1

		make_strings(user_dict)
		#print(user_dict)
		if user_dict["ID"] != "n/a":
			out["users"].append(user_dict)
		if user_dict["ID"] == "n/a":
			non_participants += 1

	#for users who have only called
	for num in call_users:
		user_dict = collections.OrderedDict()
		user_dict = collections.OrderedDict({"Date": "", 
		"ID": "", "Zip code":  get_zipcode(num), "City": get_city(num),
		"Total calls": 0, "Total texts": 0,"First contacted": "call",
		"Participated": 0, "Listened": 0,  "Uncompleted": 0, 
		"Untranscribed": 0, "Misprocessed": 0, 
		"Record": 0, "Transcribe": 0, "Listen": 0, "Watch": 0,
		"Subscribe": 0, "STOP": 0, "HELP": 0, "TRANSCRIBE": 0, "CREDIT": 0,
		"Total sent": get_reminders(num), "Received": "n/a"})
		user_messages = client.messages.list(to=hotline, from_ = num)
		user_calls = client.calls.list(to=hotline, from_ = num)
		out_going_messages = list(client.messages.list(to=num, from_ = hotline))
		user_dict["Total calls"] = str(len(user_calls))
		user_dict["Total texts"] = str(len(user_messages))
		user_dict["Date"] = get_user_date(user_messages, user_calls, start_date, end_date, num)

		user_dict["ID"] = get_hash(num)
		if user_dict["ID"] != "n/a":
			try:
				user_dict["Untranscribed"] = get_untranscribed_calls(user_dict["ID"])
			except Exception as e:
				print(e)

		if user_dict["Total sent"] >= 1:
			user_dict["Received"] = "y"

		if user_dict["Total sent"] < 1 and user_dict["Untranscribed"] > 0:
			now_date = datetime.now()
			now_simplified = datetime(now_date.year, now_date.month, now_date.day)
			if get_caller_date(num, user_calls) != "":
				diff = now_simplified - get_caller_date(num, user_calls)
				if diff.days >= 7:
					user_dict["Received"] = "n"

		if user_dict["Total sent"] == 0:
			user_dict["Received"] = "n/a"

		processing_status(out_going_messages, user_dict)
		mainmenu_messages(user_messages, user_dict)

		user_dict["Success"] = get_success(user_dict["Total sent"], num, user_dict["Untranscribed"])

		#print("Num calls: " + str(len(list(Call.objects.filter(city__code=city, from_number = num)))))
		#Add completed calls status 
		for call in Call.objects.filter(city__code=city, from_number = num):
			recordings = Recording.objects.filter(call__id=call.id)
			n = len(recordings)
			#print("Number recordings: " + str(n))
			if n == 0:
				user_dict["Listened"] += 1
			if n < 6 and n >= 1:
				user_dict["Uncompleted"] += 1 
				user_dict["Participated"] += 1
			if n >=6:
				user_dict["Participated"] += 1

		if len(user_messages) > 0:
			for c in user_calls:
				if c.end_time <= user_messages[0].date_sent:
					user_dict["First contacted"] = "call"
					break
				if c.end_time > user_messages[0].date_sent:
					user_dict["First contacted"] = "text"
					break

		if len(user_calls) == 0:
			user_dict["First contacted"] = "text"

		make_strings(user_dict)
		#print(user_dict)
		if user_dict["ID"] != "n/a":
			out["users"].append(user_dict)
		if user_dict["ID"] == "n/a":
			non_participants += 1


	out["users"] = sorted(out["users"], key=lambda k: k['Date'], reverse = True) 

	out["users"][0]["Total participants"] = str(len(out["users"]))
	out["users"][0]["Total non-participants"] = str(non_participants)

	return out

start = datetime(2020, 6, 6, 0, 0, 0)
end = datetime(2020, 6,14, 0, 0, 0)

# combo_stats("nyc", start, end)
