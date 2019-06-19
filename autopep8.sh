#!/bin/bash
cd `dirname $0`
autopep8 -i -a -r $@
