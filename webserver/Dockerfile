# python is just a convient image that includes git
FROM python:3.8 AS clone
RUN git clone https://github.com/biorack/BASTet


FROM mambaorg/micromamba:0.7.13

ENV PYTHONPATH /BASTet

RUN micromamba install -y -n base -c anaconda -c conda-forge -c bioconda \
        docutils=0.15.2 \
        gunicorn=19.9.0 \
        hdf5=1.10.5=mpi_mpich* \
        h5py=2.10.0=mpi_mpich* \
        ipython=4.2.1 \
        jinja2=2.9.6 \
        lxml=3.8.0 \
        matplotlib=2.2.4 \
        mpich=3.3.2 \
        numpy=1.16.6 \
        pillow=6.2.1 \
        pygments=2.5.2 \
        pyteomics=4.4.1 \
        python=2.7.18 \
        requests=2.25.1 \
        sphinx=1.8.5 \
        virtualenv=16.0.0 && \
    rm /opt/conda/pkgs/cache/*

# Django and WhiteNosie cannot be installed from conda as a old enough versions
# do not exist in the major conda repositories
RUN /opt/conda/bin/pip install django==1.6.11 whitenoise==2.0.6

COPY --from=clone /BASTet /BASTet
COPY ./omsi_server /src/omsi_server

WORKDIR /src/omsi_server

ENV STATIC_FILES /var/www/html/site_media/openmsi

RUN echo "from host_profiles.spin import *" > ./omsi_server/local_settings.py && \
    chmod -R a+rw /src/ && \
    mkdir -p /data/db && \
    mkdir -p /data/openmsi/omsi_data && \
    mkdir -p "${STATIC_FILES}" && \
    chown "${OMSI_USER}:${OMSI_GROUP}" "${STATIC_FILES}" && \
    chmod 777 "${STATIC_FILES}"

CMD /opt/conda/bin/python ./manage.py collectstatic --noinput && \
    /opt/conda/bin/python ./manage.py runserver 0.0.0.0:8000
