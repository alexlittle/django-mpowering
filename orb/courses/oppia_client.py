"""A simple client for publishing to Oppia"""


from __future__ import unicode_literals

from typing import BinaryIO, Dict, Text, Union

import requests


def oppia_response_message(response, default=""):
    """
    Returns the message from the Oppia server

    The Oppia server may return JSON or a plain (empty) HTML
    response.

    When there are messages, they're typically embedded in a
    JSON structure.
    """
    try:
        message = response.json()
    except ValueError:
        return default

    try:
        message = message["messages"]
    except KeyError:
        try:
            message = message["errors"]
        except KeyError:
            return default

    try:
        return "; ".join(m["message"] for m in message)
    except TypeError:
        try:
            return "; ".join(message)
        except KeyError:
            return default
    except KeyError:
        return default


class OppiaClient(object):
    """
    The Oppia server may return HTTP responses in either HTML or JSON

    """

    publish_endpoint = "/api/publish/"

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def make_request(self, url, data, files):
        # type: (Text, Dict, Dict) -> Tuple[bool, int, Text, Text]
        """
        Makes a requst and returns (status, message) in response

        Args:
            url:
            data:

        Returns:

        """
        response = requests.post(url, data=data, files=files)
        if response.status_code >= 500:
            return (
                False,
                response.status_code,
                oppia_response_message(
                    response, "There was an unknown error on the remote server"
                ),
                response.text,
            )
        if response.status_code >= 400:
            return (
                False,
                response.status_code,
                oppia_response_message(
                    response,
                    "There was an unknown problem either authenticating or submitting the data",
                ),
                response.text,
            )
        return (
            True,
            response.status_code,
            oppia_response_message(
                response, "Your course has been published to {}".format(self.host)
            ),
            response.text,
        )

    def publish_course(self, tags, is_draft, course_file):
        # type: (Text, bool, Union[Text, BinaryIO]) -> Tuple[bool, int, Text, Text]
        """
        Publishes the course zip file to Oppia publish endpoint

        Args:
            tags: string of the course tags
            is_draft: boolean flag for whether this is a draft or not
            course_file: path to the zip file

        Returns:
            a dictionary with results

        """
        if hasattr(course_file, "readlines"):
            response = self.make_request(
                self.host + self.publish_endpoint,
                data={
                    "username": self.username,
                    "password": self.password,
                    "tags": tags,
                    "is_draft": is_draft,
                },
                files={
                    "course_file": (
                        "orb_export.zip",
                        course_file,
                        "application/zip",
                        {"Expires": "0"},
                    )
                },
            )
        else:
            with open(course_file, "rb") as export_file:
                response = self.make_request(
                    self.host + self.publish_endpoint,
                    data={
                        "username": self.username,
                        "password": self.password,
                        "tags": tags,
                        "is_draft": is_draft,
                    },
                    files={"course_file": export_file},
                )

        return response
