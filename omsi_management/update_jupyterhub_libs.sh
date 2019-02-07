#!/bin/bash
#Script to update BASTet for jupyterhub

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
# cd /global/project/projectdirs/openmsi/jupyterhub_libs/anaconda/lib/python2.7/site-packages/omsi
# svn update
# chmod -R 775 omsi/
echo "DEPRECATED"
echo "The jupyterlib bastet packages uses a symbolic link to simply use the library used for data convert"
echo "Use the update_openmsi_convert to update the library manually"
