#!/bin/bash
# Script to install serial h5py in the OpenMSI conda install

#Print all commands that are executed by the script
set -o verbose
# Determine the location of our conda installation
if [ -z $CONDAPATH ]; then
    # Use the default install location
    CONDAPATH="/usr/common/contrib/m1541/openmsi-"$NERSC_HOST
else
    # Use the custom install location set by the user
    echo "CONDAPATH="$CONDAPATH;
fi

# Activate our conda environment
source $CONDAPATH/bin/activate

# Install the pacakge
conda install -y h5py

