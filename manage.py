#!/usr/bin/env python
import os
import sys
from smh_app.ssmenv import EC2ParameterStore
import dotenv
from getenv import env

AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION', 'us-east-1')
VPC_ENV = env('VPC_ENV', 'dev')
VPC_APP_NAME = env('VPC_APP_NAME', 'smhapp')
PARAMETER_STORE_PATH = "/%s/%s/" % (VPC_ENV, VPC_APP_NAME)


if __name__ == '__main__':
    dotenv.load_dotenv()
    ENVIRONMENT_VARIABLE_STRATEGY = env(
        'ENVIRONMENT_VARIABLE_STRATEGY', 'EC2_PARAMSTORE')
    # Get this from .env file (controlled by Ansible)
    if ENVIRONMENT_VARIABLE_STRATEGY == '.ENV':
        print('EVS is', ENVIRONMENT_VARIABLE_STRATEGY)
    # EC2 Parameter Store TODO Better parametrization here.
    try:
        if ENVIRONMENT_VARIABLE_STRATEGY == 'EC2_PARAMSTORE':
            print('EVS is', ENVIRONMENT_VARIABLE_STRATEGY)
            parameter_store = EC2ParameterStore(region_name=AWS_DEFAULT_REGION)
            django_parameters = parameter_store.get_parameters_by_path(
                PARAMETER_STORE_PATH, strip_path=True)
            EC2ParameterStore.set_env(django_parameters)

    except Exception as e:
        print("Exception", e)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smh_app.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
