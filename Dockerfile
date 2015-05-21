FROM zalando/ubuntu:14.04.1-3

EXPOSE 8080

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3-pip python3


ADD dist /data/dist
ADD wheelhouse /data/wheelhouse
# There will be only one wheel on /data/dist
RUN pip3 install --no-index --find-links=/data/wheelhouse /data/dist/*.whl

CMD python3 -m lizzy