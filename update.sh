#!/bin/bash

# prompt before DANGEROUS operation
while true; do
    read -n 1 -r -p "Update script will reset all the local changes. Do you wish to continue? " yn
    echo # (optional) move to a new line (because -n 1 in read)
    case $yn in
        [Yy]* ) break;; # just continue
        [Nn]* ) exit;;
        * ) echo "Please type [Y] or [N].";;
    esac
done

echo "DSD update begins."

# do a hard reset to restore any local change
# (there should not be any local change in deployment enviorment)
git reset --hard HEAD
# update from the origin
git pull
# update all the submodules (if any)
git submodule update --init --recursive --force

echo "DSD update is finished."
if [ $? -eq 0 ]; then
    echo "Please restart DSD service manually."
else
    echo "Update is finished with error [$?]!"
fi
