#!/bin/bash
#Script to update all sources of the openmsi.nersc.gov website
#
# Optional command line options:
# --update-only : Use this option to update out-of-date cache entries
#                 and add missing cache entries. This option prevents
#                 the clearing of the cache, so that any entries that
#                 are deamed up-to-date are preserved. Without the
#                 option, the cache is cleared and rebuildt from scratch.
# --clear-only : Use this option to clear the metadata-cache without
#                repopulating the cache with metadata information.
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
cd /data/openmsi/omsi_sources/omsi_server
#Run the command
python manage.py update_metadata_cache $@

