"""
Django settings for smh_app project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import dj_database_url
from django.contrib.messages import constants as messages
from getenv import env
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-bnmd8**&!68$lk(2@!_c^2=6m-v)$7no55+%@x8sjxp1e^s9!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.resources',
    'apps.sharemyhealth',
    'apps.vmi',
    'apps.affiliations',
    'apps.lockbox',
    'apps.org',
    'apps.member',
    
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smh_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates', 'smh_app'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]


WSGI_APPLICATION = 'smh_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default=env('DATABASES_CUSTOM',
                    'sqlite:///{}/db.sqlite3'.format(BASE_DIR))
    ),
}

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'apps.sharemyhealth.backends.ShareMyHealthOAuth2Backend',
    'apps.vmi.backends.VMIOAuth2Backend'
)

LOGIN_REDIRECT_URL = 'home'

# Settings for social_django
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_VMI_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.mail.mail_validation',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.debug.debug',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_core.pipeline.debug.debug'
)
SOCIAL_AUTH_SHAREMYHEALTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.debug.debug',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_core.pipeline.debug.debug'
)
# Settings for our custom OAuth backends. Note: The name of the social auth
# backend must come after 'SOCIAL_AUTH_' in these settings, in order for
# social-auth-app-django to recognize it. For example, for VMI, we define
# settings that begin with 'SOCIAL_AUTH_VMI_'.
SOCIAL_AUTH_NAME = os.environ.get('VMI_OAUTH_NAME', 'vmi')
SOCIAL_AUTH_VMI_HOST = os.environ.get('VMI_OAUTH_HOST')
SOCIAL_AUTH_VMI_KEY = os.environ.get('VMI_OAUTH_KEY')
SOCIAL_AUTH_VMI_SECRET = os.environ.get('VMI_OAUTH_SECRET')
SOCIAL_AUTH_SHAREMYHEALTH_HOST = os.environ.get('SMH_OAUTH_HOST')
SOCIAL_AUTH_SHAREMYHEALTH_KEY = os.environ.get('SMH_OAUTH_KEY')
SOCIAL_AUTH_SHAREMYHEALTH_SECRET = os.environ.get('SMH_OAUTH_SECRET')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'sitestatic'),
]

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collectedstatic')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


APPLICATION_TITLE = env('DJANGO_APPLICATION_TITLE', 'Share My Health')


ORGANIZATION_TITLE = env(
    'DJANGO_ORGANIZATION_TITLE',
    'Alliance for Better Health')

ORGANIZATION_URI = env('DJANGO_ORGANIZATION_URI', 'https://abhealth.us')

POLICY_URI = env(
    'DJANGO_POLICY_URI',
    'https://abhealth.us')

POLICY_TITLE = env('DJANGO_POLICY_TITLE', 'Privacy Policy')
TOS_URI = env('DJANGO_TOS_URI', 'https://abhealth.us')

TOS_TITLE = env('DJANGO_TOS_TITLE', 'Terms of Service')
TAG_LINE = env('DJANGO_TAG_LINE', 'Share your health data with applications, organizations, and people you trust.')

EXPLAINATION_LINE = 'This service allows Medicare beneficiaries to connect their health data to applications of their choosing.'  # noqa
EXPLAINATION_LINE = env('DJANGO_EXPLAINATION_LINE ', EXPLAINATION_LINE)

USER_DOCS_URI = "https://abhealth.us"
USER_DOCS_TITLE = "User Documentation"
USER_DOCS = "USer Docs"

DEFAULT_DISCLOSURE_TEXT = """
    This system may be monitored, recorded and
    subject to audit. Improper use of this system or
    its data may result in civil and criminal penalties.
    """

DISCLOSURE_TEXT = env('DJANGO_PRIVACY_POLICY_URI', DEFAULT_DISCLOSURE_TEXT)

CALL_MEMBER = "community member"
CALL_MEMBER_PLURAL = "community members"
CALL_ORGANIZATION = "organization"
CALL_ORGANIZATION_PLURAL = "organizations"


SETTINGS_EXPORT = [
    'DEBUG',
    'ALLOWED_HOSTS',
    'APPLICATION_TITLE',
    'STATIC_URL',
    'STATIC_ROOT',
    'ORGANIZATION_TITLE',
    'POLICY_URI',
    'POLICY_TITLE',
    'DISCLOSURE_TEXT',
    'TOS_URI',
    'TOS_TITLE',
    'TAG_LINE',
    'EXPLAINATION_LINE',
    'USER_DOCS_URI',
    'USER_DOCS',
    'USER_DOCS_TITLE',
    'CALL_MEMBER',
    'CALL_MEMBER_PLURAL',
    'CALL_ORGANIZATION',
    'CALL_ORGANIZATION_PLURAL'
]
