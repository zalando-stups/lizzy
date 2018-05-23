FROM registry.opensource.zalan.do/stups/python:latest

EXPOSE 8080

WORKDIR /app

# We can't use / with pipenv https://github.com/pypa/pipenv/issues/1648
COPY Pipfile.lock /app
RUN pipenv install --ignore-pipfile --verbose

ADD uwsgi.yaml /app
ADD setup.py /app
ADD requirements.txt /app
ADD lizzy /lizzy/app

ADD _retry.json /.aws/models/_retry.json
ADD _retry.json /root/.aws/models/_retry.json

CMD pipenv run uwsgi --yaml uwsgi.yaml
