FROM dsdgroup/jupyter:cpu

MAINTAINER Guo Quan <guoquanscu@gmail.com>

ENV REFRESHED_AT 2016-08-10

# install the core library
# Clone MXNet repo and move into it
RUN cd /root && git clone --recursive https://github.com/dmlc/mxnet && cd mxnet && \
  cp make/config.mk config.mk && \
  sed -i 's/USE_BLAS = atlas/USE_BLAS = openblas/g' config.mk

# Install Python package
# install to local python directory
#RUN cd /root/mxnet/python && python setup.py install
# or just use PYTHONPATH, as this is more flexible
ENV PYTHONPATH /mxnet/python:$PYTHONPATH

# python pakcage
# graphviz ensures the visualization of mx.viz.plot_network in ipython notebook
RUN apt-get install -y graphviz
RUN pip install graphviz

# this help us to run legacy codes, but could be harmful for current version
# ENV MXNET_EXEC_INPLACE_GRAD_SUM_CAP 888000000
