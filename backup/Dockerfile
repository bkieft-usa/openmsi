#FROM debian:buster-slim
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    sqlite3 \
    gzip \
    && rm -rf /var/lib/{apt,dpkg,cache,log}

RUN mkdir -p /data && \
    mkdir -p /backup && \
    chmod 777 /data && \
    chmod 777 /backup

ENV PREFIX=openmsi_sqlite_

CMD /bin/sh -c ' \
   export TIMESTAMP=$(date +%Y%m%d%H%M) && \
   export TEMP_FILE=$(mktemp) && \
   mkdir -p /backup/$TIMESTAMP && \
   sqlite3 /data/openmsi.sqlite ".backup $TEMP_FILE" && \
   gzip -c $TEMP_FILE > /backup/${TIMESTAMP}/${PREFIX}${TIMESTAMP}.gz && \
   rm -f ${TEMP_FILE}'
