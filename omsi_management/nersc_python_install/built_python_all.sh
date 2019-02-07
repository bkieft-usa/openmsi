#!/bin/bash
# Script to create an anaconda environment with all OpenMSI 
# packages installed

#Print all commands that are executed by the script
set -o verbose
# Determine the location of our conda installation
if [ -z $CONDAPATH ]; then 
    # Use the default install location
    CONDAPATH="/usr/common/contrib/m1541/openmsi-"$NERSC_HOST
    if [ -z $CONDA_ENABLEMPI ]; then
        CONDAPATH="/usr/common/contrib/m1541/openmsi-"$NERSC_HOST"-parallel"
    fi
else
    # Use the custom install location set by the user
    echo "CONDAPATH="$CONDAPATH;
fi


bash packages/install_miniconda.sh
bash packages/install_cython.sh
bash packages/install_numpy.sh
bash backages/install_scipy.sh
# Install parallel or serial HDF5 and install mpi4py if we want parallel
if [ -z $CONDA_ENABLEMPI ]; then
    bash packages/install_h5py_serial.sh
else
    bash packages/install_mpi4py.sh
    bash packages/install_h5py_parallel.sh
fi

# Install other base packages
bash packages/install_babel.sh
bash packages/install_bitarray.sh
bash packages/install_bokeh.sh
bash packages/install_cloudpickle.sh
bash packages/install_conda-build.sh
bash packages/install_cryptography.sh
bash packages/install_dask.sh
bash packages/install_datashape.sh
bash packages/install_decorator.sh
bash packages/install_dill.sh
bash packages/install_django.sh
bash packages/install_docutils.sh
bash packages/install_functools32.sh
bash packages/install_futures.sh
bash packages/install_ipykernel.sh
bash packages/install_ipython.sh
bash packages/install_ipython_genutils.sh
bash packages/install_ipywidgets.sh
bash packages/install_jinja2.sh
bash packages/install_joblib.sh
bash packages/install_jpeg.sh
bash packages/install_jsonschema.sh
bash packages/install_jupyter.sh
bash packages/install_jupyter_client.sh
bash packages/install_jupyter_console.sh
bash packages/install_jupyter_core.sh
bash packages/install_libnetcdf.sh
bash packages/install_libpng.sh
bash packages/install_libsodium.sh
bash packages/install_libtiff.sh
bash packages/install_libxml2.sh
bash packages/install_libxslt.sh
bash packages/install_lxml.sh
bash packages/install_matplotlib.sh
bash packages/install_memory_profiler.sh
bash packages/install_mkl.sh
bash packages/install_mkl-service.sh
bash packages/install_mysql-python.sh
bash packages/install_nb_anacondacloud.sh
bash packages/install_nb_conda.sh
bash packages/install_nb_conda_kernels.sh
bash packages/install_nbconvert.sh
bash packages/install_nbformat.sh
bash packages/install_nbpresent.sh
bash packages/install_networkx.sh
bash packages/install_nose.sh
bash packages/install_notebook.sh
bash packages/install_numba.sh
bash packages/install_numexpr.sh
bash packages/install_pandas.sh
bash packages/install_pep8.sh
bash packages/install_pickleshare.sh
bash packages/install_pillow.sh
bash packages/install_pip.sh
bash packages/install_ply.sh
bash packages/install_psutil.sh
bash packages/install_pymongo.sh
bash packages/install_pyopenssl.sh
bash packages/install_pyparsing.sh
bash packages/install_pyqt.sh
bash packages/install_pyqtgraph.sh
bash packages/install_pytables.sh
bash packages/install_pytest.sh
bash packages/install_python-dateutil.sh
bash packages/install_pyyaml.sh
bash packages/install_pyzmq.sh
bash packages/install_qtconsole.sh
bash packages/install_qtpy.sh
bash packages/install_rdkit.sh
bash packages/install_readline.sh
bash packages/install_redis.sh
bash packages/install_redis-py.sh
bash packages/install_requests.sh
bash packages/install_rope.sh
bash packages/install_ruamel_yaml.sh
bash packages/install_scikit-image.sh
bash packages/install_scikit-learn.sh
bash packages/install_setuptools.sh
bash packages/install_six.sh
bash packages/install_snowballstemmer.sh
bash packages/install_sockjs-tornado.sh
bash packages/install_sphinx.sh
bash packages/install_sphinx_rtd_theme.sh
bash packages/install_spyder.sh
bash packages/install_sqlalchemy.sh
bash packages/install_sqlite.sh
bash packages/install_ssl_match_hostname.sh
bash packages/install_statsmodels.sh
bash packages/install_sympy.sh
bash packages/install_terminado.sh
bash packages/install_tk.sh
bash packages/install_toolz.sh
bash packages/install_tornado.sh
bash packages/install_traitlets.sh
bash packages/install_unicodecsv.sh
bash packages/install_werkzeug.sh
bash packages/install_wheel.sh
bash packages/install_xlrd.sh
bash packages/install_xlsxwriter.sh
bash packages/install_xlwt.sh
bash packages/install_xz.sh
bash packages/install_yaml.sh
bash packages/install_yt.sh
bash packages/install_zeromq.sh
bash packages/install_zlib.sh

#PIP-based installs
#Pyteomics depends on numpy, matplotlib, lxml
bash packages.install_pyimzml.sh
bash packages/install_pyteomics.sh
