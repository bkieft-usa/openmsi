#!/bin/bash
# Script to create an anaconda environment with all OpenMSI 
# packages installed

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

# Set the URLs where we get Miniconda from
MINICONDA_SH=Miniconda2-latest-Linux-x86_64.sh
MINICONDA_URL=https://repo.continuum.io/miniconda/$MINICONDA_SH

# Download Miniconda
echo "Downloading miniconda"
wget $MINICONDA_URL
chmod 700 $MINICONDA_SH

# Install miniconda
echo "Create condai env at: " $CONDAPATH
bash $MINICONDA_SH -b -p $CONDAPATH
rm $MINICONDA_SH

#module load python/2.7-anaconda
# conda create -p $ENVFULLPATH numpy
#conda create --clone root -p /usr/common/contrib/m1541/openmsi-edison

#echo "Activating the env"
#source activate $ENVFULLNAME

#echo "Install required packages"
#conda install PILLOW

#conda install django=1.6.5
#
#conda install h5py
#
#conda install lxml



