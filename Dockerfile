FROM registry.opensource.zalan.do/stups/python:3.5-cd28

EXPOSE 8080

RUN apt-get update \
 && apt-get install -q -y --no-install-recommends python3-venv m4 build-essential libssl-dev libffi-dev python-dev \
 && apt-get upgrade -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ADD uwsgi.yaml /
ADD setup.py /
ADD requirements.txt /
ADD lizzy /lizzy

RUN python -m venv /lizzy_env
ENV PATH=/lizzy_env/bin:$PATH
RUN pip install -U pip setuptools wheel
RUN pip install -r requirements.txt

ADD _retry.json /.aws/models/_retry.json
ADD _retry.json /root/.aws/models/_retry.json

ADD scm-source.json /

CMD uwsgi --yaml uwsgi.yaml
