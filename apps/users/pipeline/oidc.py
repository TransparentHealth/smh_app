#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from ..models import UserProfile
from jwkest.jwt import JWT
import json

__author__ = "Alan Viars"


def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'vmi':
        # make sure there is a UserProfile object for the given User
        profile, created = UserProfile.objects.get_or_create(user=user) 
        print(profile, created)

        # Save the id_token payload to the UserProfile object
        print(f'id_token: {response.get("id_token")}')
        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            profile.id_token_payload = JWT().unpack(id_token).payload()
            print(f'payload: {profile.id_token_payload}')
            profile.save()

