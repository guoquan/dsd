FROM nvidia/cuda:7.5-cudnn4-devel
MAINTAINER Jianyong Wang <wangjianyongscu@gmail.com>

ENV REFRESHED_AT 2016-05-05

RUN apt-get update && apt-get install -y python-pip
RUN pip install --upgrade pip

RUN apt-get install -y \
  git \
  libopenblas-dev \
  libopencv-dev \
  python-dev \
  python-numpy \
  python-setuptools

# install ipython
# install jupyter
RUN pip install \
  ipython \
  jupyter \
  numpy \
  scipy \
  matplotlib
RUN pip install -U scikit-image
# expose 8888 as jupyter's default
EXPOSE 8888

# Set a seperated workspace as working directory
WORKDIR /root/workspace
# Optionally expose the workspace to the host
VOLUME ["/root/workspace"]

# Add Tini.  Tini operates as a process subreaper for jupyter. This prevents kernel crashes.
ENV TINI_VERSION v0.8.4
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

ENTRYPOINT ["/usr/bin/tini", "--"]
# Run ipython defaultly
# Run notebook for ipython defaultly
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888","--no-browser"]
