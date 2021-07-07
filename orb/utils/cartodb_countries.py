"""
 Script to update user map on CartoDB
 
 For full instructions, see the documentation at 
 https://oppiamobile.readthedocs.org/en/latest/
"""

from __future__ import unicode_literals

import argparse
import json
import time
import urllib

from orb.models import Category, Resource, Tag


def run(cartodb_account, cartodb_key):

    cartodb_table = "orbcountries_v2"

    category = Category.objects.get(slug='geography')
    countries = Tag.objects.filter(
        category=category, resourcetag__resource__status=Resource.APPROVED).distinct()

    sql = "UPDATE %s SET display=False" % (cartodb_table)
    url = "http://%s.cartodb.com/api/v2/sql?q=%s&api_key=%s" % (
        cartodb_account, sql, cartodb_key)
    u = urllib.urlopen(url)
    data = u.read()
    dataJSON = json.loads(data)
    print(dataJSON)

    for c in countries:
        no_resources = Resource.objects.filter(
            resourcetag__tag=c, status=Resource.APPROVED).count()
        sql = "UPDATE %s SET display=True, slug='%s', no_country_resources=%d WHERE name = '%s'" % (
            cartodb_table, c.slug, no_resources, c.name)
        url = "http://%s.cartodb.com/api/v2/sql?q=%s&api_key=%s" % (
            cartodb_account, sql, cartodb_key)
        u = urllib.urlopen(url)
        data = u.read()
        dataJSON = json.loads(data)
        print(c.name)
        print(dataJSON)
        time.sleep(1)

    cont_countries = Tag.objects.filter(
        category=category, parent_tag__isnull=False).distinct()
    
    for cc in cont_countries:
        no_cont_resources = Resource.objects.filter(
            resourcetag__tag=cc.parent_tag, status=Resource.APPROVED).count()
        if no_cont_resources != 0:
            sql = "UPDATE %s SET display=True, slug='%s', no_continent_resources=%d, region_slug='%s', region_name='%s' WHERE name = '%s'" % (
                cartodb_table, cc.slug, no_cont_resources, cc.parent_tag.slug, cc.parent_tag.name, cc.name)
            url = "http://%s.cartodb.com/api/v2/sql?q=%s&api_key=%s" % (
                cartodb_account, sql, cartodb_key)
            u = urllib.urlopen(url)
            data = u.read()
            dataJSON = json.loads(data)
            print(cc.name)
            print(dataJSON)
            time.sleep(1)


if __name__ == "__main__":
    import django
    django.setup()
    parser = argparse.ArgumentParser()
    parser.add_argument("cartodb_account", help="CartoDB Account Name")
    parser.add_argument("cartodb_key", help="CartoDB API Key")
    args = parser.parse_args()
    run(args.cartodb_account, args.cartodb_key)
