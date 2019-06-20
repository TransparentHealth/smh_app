#!/bin/bash
coverage run manage.py test $@
coverage report
mkdir -p coverage
coverage html
