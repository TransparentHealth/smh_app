GIT_HASH := v$(shell git rev-parse --short HEAD)

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

docker-login:
	@eval "$(shell aws ecr get-login --region $(AWS_DEFAULT_REGION) --no-include-email)"

build: docker-login
	docker build -t smhapp:latest -f .docker/Dockerfile .

push: build
	docker tag smhapp "$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/smhapp:$(GIT_HASH)"
	docker push "$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/smhapp:$(GIT_HASH)"

deploy:
	.deployment/Dockerrun.aws.json.sh $(GIT_HASH) | aws s3 cp - s3://smhapp.$(ENVIRONMENT).bucket/$(GIT_HASH)/Dockerrun.aws.json
	aws elasticbeanstalk create-application-version --application-name smhapp-dev --version-label $(GIT_HASH) --description "Version created from gitlab ci" --source-bundle S3Bucket="smhapp.$(ENVIRONMENT).bucket",S3Key="$(GIT_HASH)/Dockerrun.aws.json"
	aws elasticbeanstalk update-environment --environment-name smhapp-$(ENVIRONMENT)-env --version-label $(GIT_HASH)

init:
	.deployment/terraform init .deployment/

plan: init
	.deployment/terraform plan -var 'environment=$(ENVIRONMENT)' -var 'version=$(GIT_HASH)' .deployment/

infrastructure: init
	.deployment/terraform apply -auto-approve -var 'environment=$(ENVIRONMENT)' -var 'version=$(GIT_HASH)' .deployment/
