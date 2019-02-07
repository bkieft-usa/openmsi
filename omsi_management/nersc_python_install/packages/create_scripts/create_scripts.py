import sys

f = open('packagelist.txt', 'r')
plist = [i.rstrip('\n') for i in  f.readlines()]
pnames = [i.split("=")[0] for i in plist]
pversion = [i.split("=")[1] for i in plist]

basestring = """#!/bin/bash
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
"""

for i in pnames:

    package_string = basestring + "\n"
    package_string += "conda install -y " + i
    out_filename = "install_%s.sh" % i 
    out_file = open(out_filename, "w")
    out_file.write(package_string)
    out_file.close()
    print out_filename
    




