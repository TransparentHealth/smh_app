#!/usr/bin/env python
import os
import sys
from smh_app.ssmenv import EC2ParameterStore
import dotenv
from getenv import env
from smh_app.settings import EC2PARAMSTORE_4_ENVIRONMENT_VARIABLES


AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION', 'us-east-1')
VPC_ENV = env('VPC_ENV', 'dev')
VPC_APP_NAME = env('VPC_APP_NAME', 'smhapp')
PARAMETER_STORE_PATH = "/%s/%s/" % (VPC_ENV, VPC_APP_NAME)


if __name__ == '__main__':

    # Defaulting to .env
    # Get this from .env file from your local development environment or
    # Ansible,
    dotenv.load_dotenv()
    ENVIRONMENT_VARIABLE_STRATEGY = ".ENV"
    # EC2 Parameter Store
    try:
        if EC2PARAMSTORE_4_ENVIRONMENT_VARIABLES == "EC2_PARAMSTORE":
            parameter_store = EC2ParameterStore(region_name=AWS_DEFAULT_REGION)
            django_parameters = parameter_store.get_parameters_by_path(
                PARAMETER_STORE_PATH, strip_path=True)
            EC2ParameterStore.set_env(django_parameters)
            ENVIRONMENT_VARIABLE_STRATEGY = EC2PARAMSTORE_4_ENVIRONMENT_VARIABLES
    except Exception as e:
        print("Exception", e)
    print('ENVIRONMENT_VARIABLE_STRATEGY in manage.py is',
          ENVIRONMENT_VARIABLE_STRATEGY)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smh_app.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
