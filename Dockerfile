FROM registry.opensource.zalan.do/stups/python:3.5.2-37

EXPOSE 8080

RUN apt-get update \
 && apt-get install -q -y --no-install-recommends m4 libssl-dev build-essential libssl-dev libffi-dev python-dev \
 && apt-get upgrade -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ADD uwsgi.yaml /
ADD setup.py /
ADD requirements.txt /
ADD lizzy /lizzy
RUN pip3 install -r requirements.txt

ADD scm-source.json /

CMD uwsgi --yaml uwsgi.yaml
