#!/bin/bash
#Script to set the paths needed to install new python modules on
#openmsi.nersc.gov
#

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
  echo "ssh $USERNAME@openmsi.nersc.gov 'bash -s' < update_metadata_cache.sh"
  exit
fi


#Couple of things to be aware of
#1. RHEL based systems use yum which has a slightly different set of package names. I had to do:
# yum install libxml2 libxml2-devel libxslt-devel

#2. We are using our own python built from source in /usr/local/bin.
export PATH=/usr/local/bin/:$PATH
#3. You can now use pip to install new modules, e.g., pip install pyteomics
