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
        UserProfile.objects.get_or_create(user=user)
