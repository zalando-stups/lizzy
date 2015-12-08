FROM zalando/python:3.5.0-3

EXPOSE 8080

ADD .docker_data /data
RUN pip3 install --no-index --find-links=/data/wheelhouse /data/dist/*.whl

ADD scm-source.json /
ADD uwsgi.yaml /
ADD job.py /
CMD uwsgi --yaml uwsgi.yaml

