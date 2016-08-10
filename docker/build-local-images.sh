#!/bin/bash

# dsd-console
sudo docker build --tag dsdgroup/dsd-console ./dsd

# jupyter
sudo docker build --tag dsdgroup/jupyter:cpu ./jupyter/cpu && \
    sudo docker tag dsdgroup/jupyter:cpu dsdgroup/jupyter:latest
sudo docker build --tag dsdgroup/jupyter:gpu ./jupyter/gpu

# mxnet
sudo docker build --tag dsdgroup/mxnet:cpu ./mxnet/cpu && \
    sudo docker tag dsdgroup/mxnet:cpu dsdgroup/mxnet:latest
sudo docker build --tag dsdgroup/mxnet:gpu ./mxnet/gpu

# theano
sudo docker build --tag dsdgroup/theano:cpu ./theano/cpu && \
    sudo docker tag dsdgroup/theano:cpu dsdgroup/theano:latest
sudo docker build --tag dsdgroup/theano:gpu ./theano/gpu
