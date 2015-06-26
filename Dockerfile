FROM os-registry.stups.zalan.do/stups/zmon-worker:0.1.7

EXPOSE 8080

RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3-pip python3

ADD .docker_data /data
RUN pip3 install --no-index --find-links=/data/wheelhouse /data/dist/*.whl

ADD scm-source.json /
CMD python3 -m lizzy

