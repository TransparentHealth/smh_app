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
            org_slugs = []
            if 'organization_agent' in payload:
                for organization in payload['organization_agent']:
                    org, g_o_c = Organization.objects.get_or_create(
                        slug=organization['slug'])
                    org_slugs.append(organization['slug'])
                    org.name = organization['name']
                    org.sub = organization['sub']
                    org.website = organization['website']
                    org.phone = organization['phone_number']
                    org.picture_url = organization.get('picture', None)

                    # Now add the user to the Organization
                    org.users.add(user)
                    org.save()
                    # print(org, "Saved!")
        # remove an agent from organization if they have been removed.
        all_orgs = Organization.objects.all()
        for o in all_orgs:
            if o.slug not in org_slugs:
                o.users.remove(user)
                o.save()
