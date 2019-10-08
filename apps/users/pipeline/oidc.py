#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from jwkest.jwt import JWT
from ..models import UserProfile

__author__ = "Alan Viars"


def save_profile(backend, user, response, *args, **kwargs):
    # make sure there is a UserProfile object for the given User
    profile, created = UserProfile.objects.get_or_create(user=user)
    if backend.name == 'verifymyidentity-openidconnect':

        # Save the id_token 'sub' to the UserProfile.subject
        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            id_token_payload = JWT().unpack(id_token).payload()
            profile.subject = id_token_payload.get('sub')
            profile.save()
