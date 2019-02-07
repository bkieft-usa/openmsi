#!/bin/bash
# Script to install parallel HDF5 for the OpenMSI conda python 

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

# 1,2 are not needed since we are in the miniconda environment where h5py is not installed by default
# 1) Uninstall h5py
#conda uninstall h5py
#conda uninstall hdf5
# 2) Delete the serial HDF5 install from Anaconda
#rm $CONDA_DIR/liblibhdf5*

# 3) Download h5py sources
wget https://pypi.python.org/packages/22/82/64dada5382a60471f85f16eb7d01cc1a9620aea855cd665609adf6fdbb0d/h5py-2.6.0.tar.gz .
tar -xzf h5py-2.6.0.tar.gz 
cd h5py-2.6.0/

python setup.py clean -all
module load cray-hdf5-parallel
export H5PY_PATH=$CONDAPATH
#$CONDAPATH/lib/python2.7/site-packages
#export PYTHONPATH=$PYTHONPATH:$H5PY_PATH/lib/python2.7/site-packages

python setup.py configure -r
python setup.py configure --hdf5-version=1.8.16
python setup.py configure --mpi
export CRAYPE_LINK_TYPE=dynamic
export CC=cc
python setup.py build
python setup.py install --prefix=$H5PY_PATH

# Clean up
cd ..
rm h5py-2.6.0.tar.gz
rm -rf h5py-2.6.0/ 

# The following exports should not be needed since we in our own environment
#export PATH=/global/homes/j/jialin/anaconda2/bin/:$PATH
#export PYTHONPATH=$PYTHONPATH:/global/homes/j/jialin/anaconda2/lib/python2.7/site-packages
#module load mpi4py
#module load cray-hdf5-parallel
#export H5PY_PATH=/global/homes/j/jialin/packages/h5py-2.6.0/h5pypath
#export PYTHONPATH=$PYTHONPATH:$H5PY_PATH/lib/python2.7/site-packages
#python setup.py configure -r
#python setup.py configure --hdf5-version=1.8.16
#python setup.py configure --mpi
#export CRAYPE_LINK_TYPE=dynamic
#export CC=cc
#python setup.py build
#python setup.py install --prefix=$H5PY_PATH


