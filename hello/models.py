from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import jsonfield
from datetime import datetime, timedelta

class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)

class Document(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField()

class City(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True, default='')
    show = models.BooleanField(default=True)
    order = models.IntegerField(default=999)
    zipcodes = ArrayField(models.CharField(max_length=20, blank=True,default=''), default=list)

class Language(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    indigenous_cities = models.ManyToManyField(City, default=None)

class Participant(models.Model):
    name = models.CharField(max_length=200, blank=True, default='')
    email = models.CharField(max_length=200, blank=True, default='')
    compensation = models.BooleanField(default=False)
    notify = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True, default='')
    credit_proofed = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, default='')
    phone_number_hash = models.CharField(max_length=200, blank=True, default='')
    hash_id = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, default=None)
    zipcode = models.CharField(max_length=20, blank=True, default='')

class Call(models.Model):
    call_sid = models.CharField(max_length=200, default = '')
    from_number = models.CharField(max_length=20, default ='')
    to_number = models.CharField(max_length=20, default='')
    credit = models.CharField(max_length=100, blank=True, default='')
    received_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    # language = models.ForeignKey(Language, on_delete=models.CASCADE)
    duration = models.DurationField(default=timedelta())
    language_code = models.CharField(max_length=20, default='MNk6')
    location = models.CharField(max_length=100, blank=True, default='')
    name = models.CharField(max_length=200, blank=True, default='')
    to_notify = models.BooleanField(default=False)
    indigenous = models.BooleanField(default=False)
    valid = models.BooleanField(default=False)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, default=None)
    credit_proofed = models.BooleanField(default=False)
    compensation = models.BooleanField(default=False)
    participant = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, default=None)
    hash_id = models.CharField(max_length=200, blank=True, default='')


class Recording(models.Model):
    recording_sid = models.CharField(max_length=200)
    call = models.ForeignKey(Call, on_delete=models.CASCADE)
    order = models.IntegerField()
    url = models.URLField()
    updated_at = models.DateTimeField(auto_now=True)

class Transcription(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    alpha = models.CharField(max_length=40)
    call = models.ForeignKey(Call, on_delete=models.SET_NULL, null=True, default=None)
    participant = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, default=None)
    numeric = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MergedAudio(models.Model):
    merged_id = models.IntegerField()
    url = models.URLField()
    city_code = models.CharField(max_length=20)

class Number(models.Model):
    recording = models.ForeignKey(Recording, on_delete=models.CASCADE)
    value = models.IntegerField()
    proofed = models.BooleanField() # !!! This is now depricated
    url = models.URLField()
    correct_count =  models.IntegerField(default=0)
    incorrect_count =  models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)