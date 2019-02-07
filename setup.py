from distutils.core import setup

setup(name='omsi',
      version='0.1',
      description='OpenMSI Software Stack',
      author='Oliver Ruebel and Ben Bowen',
      author_email=' ',
      url='https://portal-auth.nersc.gov/project/openmsi/',
      packages=['omsi' , 'omsi/analysis' , 'omsi/dataformat' , 'omsi/tools' , 'omsi/viewer'],
      requires=['numpy' , 'h5py', 'django', 'requests']
     )