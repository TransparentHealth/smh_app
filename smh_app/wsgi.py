"""
WSGI config for smh_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
import dotenv
from getenv import env
from django.core.wsgi import get_wsgi_application
from .ssmenv import EC2ParameterStore

AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION', 'us-east-1')
VPC_ENV = env('VPC_ENV', 'dev')
VPC_APP_NAME = env('VPC_APP_NAME', 'smhapp')
PARAMETER_STORE_PATH = "/%s/%s/" % (VPC_ENV, VPC_APP_NAME)
ENVIRONMENT_VARIABLE_STRATEGY = env('ENVIRONMENT_VARIABLE_STRATEGY', '.ENV')

try:
    # Get this from .env file (controlled by Ansible)
    if ENVIRONMENT_VARIABLE_STRATEGY == '.ENV':
        dotenv.load_dotenv()
    # Get Via EC2 PArameter store
    if ENVIRONMENT_VARIABLE_STRATEGY == 'EC2_PARAMSTORE':
        parameter_store = EC2ParameterStore(region_name=AWS_DEFAULT_REGION)
        # Automate env (dev)
        django_parameters = parameter_store.get_parameters_by_path(
            PARAMETER_STORE_PATH, strip_path=True
        )
        EC2ParameterStore.set_env(django_parameters)
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smh_app.settings')

application = get_wsgi_application()
