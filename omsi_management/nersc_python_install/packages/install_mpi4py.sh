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

# Activate our conda environment
source $CONDAPATH/bin/activate

# Download mpi4py
mpi4py=mpi4py-2.0.0

mpi4py_tgz=$mpi4py.tar.gz
rm -rf $mpi4py $mpi4py_tgz
wget https://bitbucket.org/mpi4py/mpi4py/downloads/$mpi4py_tgz -O $mpi4py_tgz
tar zxvf $mpi4py_tgz
cd $mpi4py

if [ "$NERSC_HOST" = "cori" ]; then
    python setup.py build --mpicc=$(which cc)
    python setup.py build_exe --mpicc="$(which cc) -dynamic"
elif [ "$NERSC_HOST" = "edison" ]; then
    # cancels out the -dynamic...
    LDFLAGS="-shared" python setup.py build --mpicc=$(which cc)
    python setup.py build_exe --mpicc=$(which cc)
else
    echo "Unrecognized NERSC_HOST: $NERSC_HOST"
    exit 137
fi

python setup.py install
cd ..
rm -rf $mpi4py $mpi4py_tgz


