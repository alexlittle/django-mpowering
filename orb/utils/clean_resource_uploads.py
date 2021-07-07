"""
Script to validate urls
"""
from __future__ import unicode_literals

import os

import django
from django.conf import settings

from orb.models import Resource, ResourceFile, Tag


def run():
    print("Cleaning resource uploads")
    print("-------------------------")
    rootDir = os.path.join(settings.MEDIA_ROOT, 'resource')
    for dirName, subdirList, fileList in os.walk(rootDir):
        relative_dir = dirName.replace(settings.MEDIA_ROOT, '')
        for fname in fileList:
            file_name = '%s/%s' % (relative_dir, fname)

            try:
                resource_file = ResourceFile.objects.get(file=file_name)
            except ResourceFile.DoesNotExist:
                print(file_name + " not found in database ")
                try:
                    os.remove(os.path.join(dirName, fname))
                    print(fname + ": DELETED")
                except OSError:
                    print("could not delete: " + fname)

                print("---")

    print("Cleaning tag uploads")
    print("--------------------")
    upload_sub_dir = 'tag'
    rootDir = os.path.join(settings.MEDIA_ROOT, upload_sub_dir)
    for dirName, subdirList, fileList in os.walk(rootDir):
        relative_dir = dirName.replace(settings.MEDIA_ROOT, '')
        for fname in fileList:
            file_name = '%s/%s' % (relative_dir, fname)
            # skip files in the root dir
            if relative_dir == upload_sub_dir:
                continue
            try:
                tag_image = Tag.objects.get(image=file_name)
            except Tag.DoesNotExist:
                print(file_name + " not found in database ")
                try:
                    os.remove(os.path.join(dirName, fname))
                    print(fname + ": DELETED")
                except OSError:
                    print("could not delete: " + fname)

                print("---")

    print("Cleaning resourceimage uploads")
    print("--------------------")

    upload_sub_dir = 'resourceimage'
    rootDir = os.path.join(settings.MEDIA_ROOT, upload_sub_dir)
    for dirName, subdirList, fileList in os.walk(rootDir):
        relative_dir = dirName.replace(settings.MEDIA_ROOT, '')
        for fname in fileList:
            file_name = '%s/%s' % (relative_dir, fname)
            # skip files in the root dir
            if relative_dir == upload_sub_dir:
                continue
            try:
                resource_image = Resource.objects.get(image=file_name)
            except Resource.DoesNotExist:
                print(file_name + " not found in database ")
                try:
                    os.remove(os.path.join(dirName, fname))
                    print(fname + ": DELETED")
                except OSError:
                    print("could not delete: " + fname)

                print("---")

if __name__ == "__main__":
    django.setup()
    run()
