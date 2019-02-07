#!/bin/bash
# Install package for OpenMSI conda python

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

# Install the package

# Usee --disable-pip-version-check to avoid pip from hanging after the install is complete
pip install --disable-pip-version-check --verbose pyimzml
