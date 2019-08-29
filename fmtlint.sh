#!/bin/bash
PATHS="apps libs smh_app"
isort -q -rc $PATHS
black -q $PATHS
flake8
