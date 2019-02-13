SMH Organization
------------------------

- Python 3.7.x
- `pip <http://www.pip-installer.org/>`_ >= 18.0
- `virtualenv <http://www.virtualenv.org/>`_ >= 16.0.0
- `virtualenvwrapper <http://pypi.python.org/pypi/virtualenvwrapper>`_ >= 4.8.2
- Postgres >= 10.4 (latest for AWS RDS right now)
- git >= 2.19.0


Django version
------------------------

Django 2.1.5


Getting Started
------------------------

First clone the repository from Github and switch to the new directory::

    $ git clone git@github.com:TransparentHealth/smh-organization
    $ cd smh-organization

To setup your local environment you can use the quickstart make target `setup`, which will
install Python (via pip) into a virtualenv named "smh_organization",
and create a database via Postgres named "smh_organization" with all migrations run::

    $ make setup
    $ workon smh_organization