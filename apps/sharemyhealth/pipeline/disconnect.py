#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from social_django.models import UserSocialAuth
import requests
from django.conf import settings
import logging
from memoize import delete_memoized
from ...member.utils import fetch_member_data
__author__ = "Alan Viars"

logger = logging.getLogger('smhapp_.%s' % __name__)


def delete_memory(backend, user, *args, **kwargs):
    """This should prevent a view of data after disconnect"""
    if backend.name == 'sharemyhealth':
        delete_memoized(fetch_member_data, user, backend.name)


def remote_revoke(backend, user, *args, **kwargs):
    """Perform a remote revocation of access_token and refresh_token"""
    if backend.name == 'sharemyhealth':

        usas = UserSocialAuth.objects.filter(user=user, provider=backend.name)
        for usa in usas:

            # revoke the access_token
            post_data = {"client_id": settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY,
                         "client_secret": settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET,
                         "token": usa.extra_data['access_token']}

            request_response_access_token = requests.post(
                backend.REVOKE_TOKEN_URL, data=post_data)

            logger.info("access_token revocation to %s returned %s status for user  %s %s." % (backend.REVOKE_TOKEN_URL,
                                                                                               request_response_access_token.status_code,
                                                                                               user.first_name.title(),
                                                                                               user.last_name.title(),))

            if request_response_access_token.status_code != 200:
                logger.error("access_token revocation to %s returned %s status for user  %s %s." % (backend.REVOKE_TOKEN_URL,
                                                                                                    request_response_access_token.status_code,
                                                                                                    user.first_name.title(),
                                                                                                    user.last_name.title(),))

            # revoke the refresh_token
            post_data = {"client_id": settings.SOCIAL_AUTH_SHAREMYHEALTH_KEY,
                         "client_secret": settings.SOCIAL_AUTH_SHAREMYHEALTH_SECRET,
                         "token": usa.extra_data['refresh_token']}

            request_response_refresh_token = requests.post(
                backend.REVOKE_TOKEN_URL, data=post_data)

            logger.info("refresh token revocation to %s returned %s status for user  %s %s." % (backend.REVOKE_TOKEN_URL,
                                                                                                request_response_refresh_token.status_code,
                                                                                                user.first_name.title(),
                                                                                                user.last_name.title(),))

            if request_response_refresh_token.status_code != 200:
                logger.error("refresh token revocation to %s returned %s status for user  %s %s." % (backend.REVOKE_TOKEN_URL,
                                                                                                     request_response_refresh_token.status_code,
                                                                                                     user.first_name.title(),
                                                                                                     user.last_name.title(),))

            # save the responses to the pipeline
            response = {'request_response_refresh_token_sharemyhealth': request_response_refresh_token,
                        'request_response_access_token_sharemyhealth': request_response_access_token}
        return response
