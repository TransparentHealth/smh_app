FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -  \
	& apt-get install -y nodejs
RUN pip install -r requirements.txt
RUN pip install django-extensions
RUN pip install Werkzeug
RUN pip install pyOpenSSL
