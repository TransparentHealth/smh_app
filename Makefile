setup:
	virtualenv -p `which python3.7` $(WORKON_HOME)/smh_organization
	$(WORKON_HOME)/smh_organization/bin/pip install -U pip wheel
	$(WORKON_HOME)/smh_organization/bin/pip install -Ur requirements.txt
	$(WORKON_HOME)/smh_organization/bin/pip freeze
	echo "DJANGO_SETTINGS_MODULE=smh_organization.settings" > .env
	createdb -E UTF-8 smh_organization
	$(WORKON_HOME)/smh_organization/bin/python manage.py migrate
	@echo
	@echo "The smh_organization project is now setup on your machine."
	@echo "Run the following commands to activate the virtual environment and run the"
	@echo "development server:"
	@echo
	@echo "workon smh_organization"
	@echo "python manage.py runserver"