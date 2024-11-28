#!/bin/bash
export PS1="\u@rocmtorch:\w\$ "
echo "USER=${USER}"

#This will trap the exit on the bash shell and then call the python script to copy the docker  created files in //home/${USER} to DOCKER-DIRS-ON-HOST
trap "gosu ${USER} /usr/bin/bash -c 'cd /home/${USER} && /opt/conda/envs/py_3.10/bin/python ./docker-symlink.py --exit --config ./config_symlink.xml'" EXIT
#Create the symlink
gosu ${USER} /usr/bin/bash -c 'cd /home/${USER} && /opt/conda/envs/py_3.10/bin/python ./docker-symlink.py --config ./config_symlink.xml'
#Switch to the user
gosu ${USER} "$@"
