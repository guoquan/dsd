#!/bin/bash

# dsd-console
sudo docker build --tag dsdgroup/dsd-console ./dsd

# jupyter
sudo docker build --tag dsdgroup/jupyter:cpu ./jupyter/cpu \
    && sudo docker tag dsdgroup/jupyter:cpu dsdgroup/jupyter:latest
sudo docker build --tag dsdgroup/jupyter:gpu ./jupyter/gpu
