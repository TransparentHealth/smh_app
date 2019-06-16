#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from ...org.models import Organization
from ...users.models import UserProfile
from jwkest.jwt import JWT

__author__ = "Alan Viars"


def create_or_update_org(backend, user, response, *args, **kwargs):
    if backend.name == 'vmi':
        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            payload = parsed_id_token.payload()

            if 'organization_agent' in payload:
                for organization in payload['organization_agent']:
                    org, g_o_c = Organization.objects.get_or_create(
                        slug=organization['slug'])
                    org.name = organization['name']
                    org.sub = organization['sub']
                    org.website = organization['website']
                    org.phone = organization['phone_number']
                    org.picture_url = organization['picture']
                    org.save()
                    print(org, "Saved!")


def set_user_type(backend, user, response, *args, **kwargs):

    user_type = "M"
    up, g_o_c = UserProfile.objects.get_or_create(user=user)
    if backend.name == 'vmi':
        user_type = "M"
        up, g_o_c = UserProfile.objects.get_or_create(user=user)
        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            payload = parsed_id_token.payload()
            if 'organization_agent' in payload:
                if len(payload['organization_agent']) > 0:
                    user_type = "O"
    up.user_type = user_type
    up.save()
