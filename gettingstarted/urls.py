from django.urls import path, include

from django.contrib import admin

admin.autodiscover()

import hello.views

urlpatterns = [
    path("", hello.views.index, name="index"),
    path("admin/", admin.site.urls),
    path('transcriber_stats/<start_month>/<start_day>/<end_month>/<end_day>', hello.views.transcriber_stats, name="transcriber_stats"),
    path('languages_stats/<city>/<start_month>/<start_day>/<end_month>/<end_day>', hello.views.languages_stats, name="langauges_stats"),
    path('new_languages/<start_month>/<start_day>/<end_month>/<end_day>', hello.views.new_languages_stats, name="new_stats"),
    path('stats/<city>/<start_month>/<start_day>/<end_month>/<end_day>', hello.views.stats, name="stats"),
    path('untranscribed_languages/', hello.views.untranscribed_languages, name="untranscribed")
]
