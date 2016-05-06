FROM wangjianyong/jupyter
MAINTAINER Jianyong Wang <wangjianyongscu@gmail.com>
ENV REFRESHED_AT 2016-05-05

#############
RUN apt-get update && apt-get install -y \
  git \
  libopenblas-dev \
  libopencv-dev \
  python-dev \
  python-numpy \
  python-setuptools

# install the core library
# Clone MXNet repo and move into it
RUN cd /root && git clone --recursive https://github.com/dmlc/mxnet && cd mxnet && \
# Copy config.mk
  cp make/config.mk config.mk && \
# Set OpenBLAS
  sed -i 's/USE_BLAS = atlas/USE_BLAS = openblas/g' config.mk && \
# Set CUDA flag
  sed -i 's/USE_CUDA = 0/USE_CUDA = 0/g' config.mk && \
  sed -i 's/USE_CUDA_PATH = NONE/USE_CUDA_PATH = NONE' config.mk && \
# Set cuDNN flag
# TODO: Change when cuDNN v4 supported
  sed -i 's/USE_CUDNN = 0/USE_CUDNN = 0/g' config.mk && \
# Make 
  make -j"$(nproc)"

# Install Python package
RUN cd /root/mxnet/python && python setup.py install
#############

# python pakcage
# graphviz ensures the visualization of mx.viz.plot_network in ipython notebook
RUN apt-get install -y python-numpy wget unzip graphviz
# RUN cd ~/mxnet/python && python setup.py install
ENV PYTHONPATH /mxnet/python
ENV MXNET_EXEC_INPLACE_GRAD_SUM_CAP 512000000
RUN pip install graphviz