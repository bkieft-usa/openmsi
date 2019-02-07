#!/bin/bash
#Script to update all sources of the openmsi.nersc.gov website

#Print all commands that are executed by the script
set -o verbose

#Check that we are on openmsi.nersc.gov when we run this script
HOST=$(hostname --long)
USERNAME=$(id -un)
if [ "$HOST" != "sgn03.nersc.gov" ]; then
  echo ""
  echo "WARNING"
  echo "This script must be executed on openmsi.nersc.gov."
  echo "Please log into openmsi.nersc.gov or run the script via ssh, e.g,"
  echo "ssh $USERNAME@openmsi.nersc.gov 'bash -s' < update_openmsi_website.sh"
  exit
fi

#Update the openmsi-tk repo and set permissions
cd /data/openmsi/bastet
git fetch origin
git reset --hard origin/master
chgrp -R m1541 *
chmod -R 2775 *
setfacl -R -m u:apache:rwx omsi
#Update the openmsi sources repo and set permissions
cd /data/openmsi/omsi_sources
svn update
chgrp -R m1541 *
chmod -R 2775 *
setfacl -R -m u:apache:rwx omsi_server
#Tell apache that the data has changed
touch omsi_server/omsi.wsgi
#Collect the static data
cd /data/openmsi/omsi_sources/omsi_server
python manage.py collectstatic
