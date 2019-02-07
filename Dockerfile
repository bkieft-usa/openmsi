FROM conda/miniconda2

RUN apt-get -y update && apt-get -y install build-essential git vim
RUN  conda install numpy h5py  matplotlib pil

RUN git clone https://github.com/biorack/BASTet
##  PYTHONPATH=/src/omsi_sources/BASTet/ python ./manage.py runserver


ADD requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

ENV PYTHONPATH /BASTet
ADD . /src/
RUN chmod -R a+rw /src/

WORKDIR /src/omsi_server
RUN echo "from host_profiles.spin import *" > ./omsi_server/local_settings.py
RUN mkdir -p /data/db

CMD python ./manage.py runserver 0.0.0.0:8000
