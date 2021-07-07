"""
 Script to get user locations based on their IP address in the Tracker model
 
 For full instructions, see the documentation at 
 https://oppiamobile.readthedocs.org/en/latest/
"""

from __future__ import unicode_literals

import json
import time
import urllib2

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from orb.analytics.models import UserLocationVisualization
from orb.models import ResourceTracker, SearchTracker, TagTracker


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        tracker_ip_hits = ResourceTracker.objects.all().values(
            'ip').annotate(count_hits=Count('ip'))
    
        for t in tracker_ip_hits:
            # lookup whether already cached in db
            try:
                cached = UserLocationVisualization.objects.get(
                    ip=t['ip'], source='resource')
                cached.hits = t['count_hits']
                cached.save()
                print("resource hits updated")
            except UserLocationVisualization.DoesNotExist:
                self.update_via_ipstack(t, 'resource')
    
        search_ip_hits = SearchTracker.objects.all().values(
            'ip').annotate(count_hits=Count('ip'))
        for s in search_ip_hits:
            # lookup whether already cached in db
            try:
                cached = UserLocationVisualization.objects.get(
                    ip=s['ip'], source='search')
                cached.hits = s['count_hits']
                cached.save()
                print("search hits updated")
            except UserLocationVisualization.DoesNotExist:
                self.update_via_ipstack(s, 'search')
    
        tag_ip_hits = TagTracker.objects.all().values(
            'ip').annotate(count_hits=Count('ip'))
        for t in tag_ip_hits:
            # lookup whether already cached in db
            try:
                cached = UserLocationVisualization.objects.get(
                    ip=t['ip'], source='tag')
                cached.hits = t['count_hits']
                cached.save()
                print("tag hits updated")
            except UserLocationVisualization.DoesNotExist:
                self.update_via_ipstack(t, 'tag')


    def update_via_ipstack(self, t, source):
        url = 'http://api.ipstack.com/%s?access_key=%s' % (t['ip'], settings.IP_STACK_API_KEY)
        print(t['ip'] + " : " + url)
        try:
            u = urllib2.urlopen(urllib2.Request(url), timeout=10)
            data = u.read()
            data_json = json.loads(data, "utf-8")
            print(data_json)
        except:
            return
    
        try:
            if data_json['latitude'] != 0 and data_json['longitude'] != 0:
                viz = UserLocationVisualization()
                viz.ip = t['ip']
                viz.lat = data_json['latitude']
                viz.lng = data_json['longitude']
                viz.hits = t['count_hits']
                viz.region = data_json['city'] + " " + data_json['region_name']
                viz.country_code = data_json['country_code']
                viz.country_name = data_json['country_name']
                viz.geonames_data = data_json
                viz.source = source
                viz.save()
        except:
            pass
        time.sleep(1)
