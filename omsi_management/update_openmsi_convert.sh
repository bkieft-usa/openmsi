#!/bin/bash
#Script to update all sources of the openmsi.nersc.gov website

#Print all commands that are executed by the script
set -o verbose

#Check that we are on openmsi.nersc.gov when we run this script
HOST=$(hostname --long)
USERNAME=$(id -un)
if [ "$HOST" == "sgn03.nersc.gov" ]; then
  echo ""
  echo "WARNING"
  echo "This script must be executed on edison, carver, hopper, or poral-auth as."
  echo "openmsi.nersc.gov has read-only access to project"
  echo "ssh $USERNAME@edison.nersc.gov 'bash -s' < update_openmsi_website.sh"
  exit
fi

#Update the openmsi-tk repo and set permissions
cd /project/projectdirs/openmsi/omsi_processing_status/bastet
git fetch origin
git reset --hard origin/master
cd /project/projectdirs/openmsi/omsi_processing_status
chgrp -R m1541 bastet/
chmod -R 2770 bastet/
setfacl -R -m u:48:rwx bastet/

