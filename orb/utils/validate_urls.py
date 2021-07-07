"""
Script to validate urls
"""
from __future__ import unicode_literals

import datetime
import time
import urllib2

import django

from orb.emailer import link_checker_results
from orb.models import ResourceURL, Tag


def run():
    pass

    resource_urls = []
    today_number = datetime.datetime.today().weekday()

    urls = ResourceURL.objects.all()
    for u in urls:
        if u.id % 7 != today_number:
            continue

        time.sleep(10)
        req = urllib2.Request(
            u.url, headers={'User-Agent': 'COVID-19 Library Link Validator', })
        try:
            connection = opener.open(request)
            print u.url + " : " + str(connection.code)
        except:
            print "ERROR connecting to " + u.url
            print u.url + " : " + str(connection.code)
            resource_urls.append(u)

    tags = []

    urls = Tag.objects.exclude(external_url=None).exclude(external_url='')
    for u in urls:
        if u.id % 7 != today_number:
            continue

        time.sleep(10)
        req = urllib2.Request(u.external_url, headers={
                              'User-Agent': 'Mozilla/5.0', })

        try:
            connection = opener.open(request)
            print u.external_url + " : " + str(connection.code)
        except:
            print "ERROR connecting to " + u.url
            print u.external_url + " : " + str(connection.code)
            tags.append(u)

    print resource_urls
    print tags

    if len(resource_urls) > 0 or len(tags) > 0:
        link_checker_results(resource_urls, tags)

if __name__ == "__main__":
    django.setup()
    run()
