FROM zalando/ubuntu:14.04.1-3

EXPOSE 8080

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3-pip python3

ADD .docker_data /data
RUN pip3 install --no-index --find-links=/data/wheelhouse /data/dist/*.whl

CMD python3 -m lizzy