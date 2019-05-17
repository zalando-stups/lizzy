FROM registry.opensource.zalan.do/stups/python:latest

RUN apt-get update && apt-get install -y python3-dev && apt clean && rm -rf /var/tmp/* /tmp/* /var/lib/apt/*

EXPOSE 8080

WORKDIR /app

ENV PIPENV_VENV_IN_PROJECT true

# We can't use / with pipenv https://github.com/pypa/pipenv/issues/1648
COPY Pipfile.lock /app
RUN pipenv install --ignore-pipfile

ADD uwsgi.yaml /app
ADD lizzy /app/lizzy

ADD _retry.json /.aws/models/_retry.json
ADD _retry.json /root/.aws/models/_retry.json

CMD pipenv run uwsgi --yaml uwsgi.yaml
