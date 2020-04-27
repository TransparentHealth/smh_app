SMH App |build-status|
----------------------

Share My Health app is a front-facing application designed for use by Community
Based Organizations (CBOs), care coordinators, and community members.
Its primary purpose is to improve care coordination by sharing health information
with relevant parties.

* Allow a member(patient) to connect to their health information from one or more data source.
* Allow a member(patient) to view the health information information.
* Allow a member to share access to the information with one or more Organizations.
* Allow an agent of a community-based organization (CBO) to view the health information.

The Share My Health App is a relying party to Verify My Identity, a certified  OpenID Connect
Identity Provider.  As a prerequisite to a Member gaining access to health
information, and identity assurance level of 2 (according to NIS) must first be
established. While this can happen in multiple ways, the primary method for this
application is an Organization's agent functions as a trusted referee and
corroborates the claimed identity with some real-world evidence.
This will most often occur upon the initial organization-assisted
member enrollment.

The Share My Health App functions as an OAuth2 client for each data source a member connects. 
Data sources typically expose health information in FHIR format.  This application will launch
in the Capital region of New York.  The first data source will be the Health 
Information Exchange of New York (HIXNY).

For more background information, please see the following links:

- https://www.hl7.org/fhir/overview.html
- https://pages.nist.gov/800-63-3/
- https://openid.net/connect/
- https://www.carinalliance.com/

 


Dependency Versions
-------------------

- Python 3.7.x
- Django 3.0
- `pip <http://www.pip-installer.org/>`_ >= 18.0
- `virtualenv <http://www.virtualenv.org/>`_ >= 16.0.0
- `virtualenvwrapper <http://pypi.python.org/pypi/virtualenvwrapper>`_ >= 4.8.2
- Postgres >= 10.4 (latest for AWS RDS right now)
- git >= 2.19.0

Getting Started
------------------------

First clone the repository from Github and switch to the new directory::

    $ git clone git@github.com:TransparentHealth/smh_app
    $ cd smh_app

To setup your local environment you can use the quickstart make target `setup`, which will
install Python (via pip) into a virtualenv named "smh_app",
and create a database via Postgres named "smh_app" with all migrations run::

    $ mkvirtualenv smh_app
    $ workon smh_app
    $ cd .assets
    $ make build
    $ python manage.py migrate
    $ python manage.oy runserver



Development
------------------------

to setup a watcher on all sass files and compile sass (from main directory)::

    $ npm run sass --prefix style


.. |build-status| image:: https://travis-ci.org/TransparentHealth/smh_app.svg?branch=master
    :target: https://travis-ci.org/TransparentHealth/smh_app

VMI and ShareMyHealth
------------------------
This project also communicates with two other apps (Vereify My Identity and OAuth2.org the OAuth2 Provider).
You will need to setup these providers to communicate with ``smh_app`` by:

- going to the VMI and ShareMyHealth servers, creating an account on each, and
  registering an application on each server
- adding the appropriate values from the above step for each application to your ``.env`` file. A
  sample ``.env`` file is provided in ``.env-sample``.
