FROM python:3
ENV PYTHONUNBUFFERED 1
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r dev-requirements.txt
RUN pip install django-extensions
RUN pip install Werkzeug
RUN pip install pyOpenSSL
