TODO: Update the jupyterhub kernel JSON to point to the new location
TODO: Add scripts for all the other packages
TODO: Test that $CONDA_ENABLEMPI is actually working in the ./build_python_all script


**Building Conda Python**

* To rebuild the complete environment call: ./built_python_all.sh
* The install location is determined by the $CONDAPATH environment variable. 
  If the variable is not set, then the default /usr/common/contrib/m1541/openmsi-$NERSC_HOST 
  will be used. To customize the location where the install should be created, 
  set the $CONDAPATH environment variable before calling the scripts.
* By default mpi and parallel HDF5 are disabled to avoid problems with
  running on NERSC login nodes. To enable parallel hdf5 and mpi set
  the environment variable $CONDA_ENABLEMPI before running the ./build_python_all 
  script 
* To install a particular package run the corresponding bash script 
  from the packages folder


**Installing a custom Kernel for Jupyterhub**

The example Kernel for OpenMSI is located in the jupyterhub/ folder. To add the OpenMSI 
Jupyter kernel to jupyter.nersc.gov, simply copy
jupyterhub/opemsi_nersc_jupyter_kernel.json to $HOME/.ipython/kernels/openmsi/kernel.json

NOTE: You have to create the kernels/openmsi folder first.

