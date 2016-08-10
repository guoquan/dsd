FROM dsdgroup/jupyter:cpu

MAINTAINER Guo Quan <guoquanscu@gmail.com>

ENV REFRESHED_AT 2016-08-10

# Install python-nose
RUN apt-get update && apt-get install -y python-nose

# Install bleeding-edge Theano
RUN pip install --upgrade --no-deps git+git://github.com/Theano/Theano.git
