# FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
FROM python:3.6-stretch

MAINTAINER luckydonald

ARG FOLDER

RUN set -x \
    # make überstart executable
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
    # Install nginx, and stuff
        ca-certificates \
        gettext-base \
    # utilities
        nano \
    # install python wsgi
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Sane defaults for pip
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on

WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]

COPY $FOLDER/entrypoint.sh      /
COPY $FOLDER/uwsgi.ini          /config/
COPY $FOLDER/requirements.txt   /config/
RUN pip install -r /config/requirements.txt

COPY $FOLDER/code /app
