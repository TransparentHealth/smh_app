#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from jwkest.jwt import JWT

__author__ = "Alan Viars"


def get_username(strategy, details, backend, user, response, *args, **kwargs):
    # The subject id is the username.
    if backend.name == 'verifymyidentity-openidconnect':
        if 'id_token' in response.keys():
            id_token = response.get('id_token')
            parsed_id_token = JWT().unpack(id_token)
            payload = parsed_id_token.payload()
            return {'username': payload['sub']}
    return
