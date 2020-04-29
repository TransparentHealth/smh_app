#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from social_django.models import UserSocialAuth
import requests
from django.conf import settings

__author__ = "Alan Viars"


def remote_revoke(backend, user, *args, **kwargs):
    if backend.name == 'sharemyhealth':

        usas = UserSocialAuth.objects.filter(user=user)
        for usa in usas:
            print("REVOKE!!!!!!!!!", usa.extra_data)

            post_data = {"client_id": settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY,
                         "client_secret": settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET,
                         "token": usa.extra_data['access_token']}

            request_response_access_token = requests.post(
                backend.REVOKE_TOKEN_URL, data=post_data)

            # revoke the refresh_token
            post_data = {"client_id": settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY,
                         "client_secret": settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET,
                         "token": usa.extra_data['refresh_token']}

            request_response_refresh_token = requests.post(
                backend.REVOKE_TOKEN_URL, data=post_data)

            # implicit return value.
            response = {'request_response_refresh_token': request_response_refresh_token,
                        'request_response_access_token': request_response_access_token}
            return response
