#!/bin/bash
#Script to setup folder for new users
#
# Required command-line parameters:
# 
# <username> : The username of the user for which the folder structure should be created

#Print all commands that are executed by the script
set -o verbose

#Check if a username was supplied
if [ -z "$1" ]
  then
    echo "No argument supplied"
    echo "Execute the script via: "
    echo "./create_userfolders.sh <username>"
    exit 1
fi

#Create an original data folder for the user so that the user can upload data
cd /global/project/projectdirs/openmsi/original_data 
mkdir $1
#Set permisions for the new folder: i) group=openmsi, ii) rwxrwx---, iii) rwx for user 
chgrp openmsi $1
chmod 2770 $1
setfacl -R -m u:$1:rwx $1
setfacl -R -m u:48:rwx $1

#Create a private data folder for the user so that the user can have private data on OpenMSI
cd /global/project/projectdirs/openmsi/omsi_data_private
mkdir $1
#Set permisions for the new folder: i) group=openmsi, ii) rwxrwx---, iii) rwx for user, iv) rwx for apache
chgrp openmsi $1
chmod 2770 $1
setfacl -R -m u:$1:rwx $1
setfacl -R -m u:48:rwx $1


