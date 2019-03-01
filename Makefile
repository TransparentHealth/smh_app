setup:
	virtualenv -p `which python3.7` $(WORKON_HOME)/smh_app
	$(WORKON_HOME)/smh_app/bin/pip install -U pip wheel
	$(WORKON_HOME)/smh_app/bin/pip install -Ur requirements.txt
	$(WORKON_HOME)/smh_app/bin/pip freeze
	echo "DJANGO_SETTINGS_MODULE=smh_app.settings" > .env
	createdb -E UTF-8 smh_app
	$(WORKON_HOME)/smh_app/bin/python manage.py migrate
	@echo
	@echo "The smh_app project is now setup on your machine."
	@echo "Run the following commands to activate the virtual environment and run the"
	@echo "development server:"
	@echo
	@echo "workon smh_app"
	@echo "python manage.py runserver"
