#!/bin/bash
#Script to update all sources of the openmsi.nersc.gov website
#
# Optional command line options:
#
# --save : Save the results of the statistics to file
# --managed-only: Compile statistics only for files managed in the database
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

#Change the directory
cd /data/openmsi/system_stats
#Run the command
python /data/openmsi/omsi_sources/omsi_server/manage.py system_stats $@

