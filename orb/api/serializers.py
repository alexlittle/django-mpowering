# orb/api/serializers.py
from __future__ import unicode_literals

import json

from tastypie.serializers import Serializer

JSON_INDENT = 4


class PrettyJSONSerializer(Serializer):

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data,
                          sort_keys=True, ensure_ascii=False, indent=JSON_INDENT)


class ResourceSerializer(Serializer):

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)

        return json.dumps(data,
                          sort_keys=True, ensure_ascii=False, indent=JSON_INDENT)

    def format_resource(self, data):
        # refactor tags
        if 'tags' in data:
            for tag in data['tags']:
                del tag['id']
                del tag['create_date']
                for qkey, qvalue in tag['tag'].items():
                    if qvalue is not None:
                        tag[qkey] = qvalue
                del tag['tag']

        return data
