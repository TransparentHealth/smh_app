SMH App
------------------------

- Python 3.7.x
- `pip <http://www.pip-installer.org/>`_ >= 18.0
- `virtualenv <http://www.virtualenv.org/>`_ >= 16.0.0
- `virtualenvwrapper <http://pypi.python.org/pypi/virtualenvwrapper>`_ >= 4.8.2
- Postgres >= 10.4 (latest for AWS RDS right now)
- git >= 2.19.0


Django version
------------------------

Django 2.1.7


Getting Started
------------------------

First clone the repository from Github and switch to the new directory::

    $ git clone git@github.com:TransparentHealth/smh_app
    $ cd smh_app

To setup your local environment you can use the quickstart make target `setup`, which will
install Python (via pip) into a virtualenv named "smh_app",
and create a database via Postgres named "smh_app" with all migrations run::

    $ make setup
    $ workon smh_app

Development
------------------------

to setup a watcher on all sass files and compile sass (from main directory)::

    $ npm run sass --prefix style


