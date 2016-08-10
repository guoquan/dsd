FROM dsdgroup/jupyter:gpu

MAINTAINER Guo Quan <guoquanscu@gmail.com>

ENV REFRESHED_AT 2016-08-10

# install the core library
# Clone MXNet repo and move into it
RUN cd /root && git clone --recursive https://github.com/dmlc/mxnet && cd mxnet && \
  cp make/config.mk config.mk && \
  sed -i 's/USE_BLAS = atlas/USE_BLAS = openblas/g' config.mk && \
  sed -i 's/USE_CUDA = 0/USE_CUDA = 1/g' config.mk && \
  sed -i 's/USE_CUDA_PATH = NONE/USE_CUDA_PATH = \/usr\/local\/cuda/g' config.mk && \
  sed -i 's/USE_CUDNN = 0/USE_CUDNN = 1/g' config.mk && \
  make -j"$(nproc)" ADD_LDFLAGS=-L/usr/local/cuda/lib64/stubs

ENV LD_LIBRARY_PATH /usr/local/cuda/lib64:$LD_LIBRARY_PATH

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
