FROM nvidia/cuda:7.5
MAINTAINER Guo Quan <guoquan@gmail.com>

ENV REFRESHED_AT 2016-05-12
RUN apt-get update

# Python: we are python based
RUN apt-get install -y git python python-dev python-pip python-setuptools && \
    pip install -U pip

# Nginx: front-end web server
RUN apt-get install -y nginx

# Jupyter: we develop with jupyter
RUN pip install ipython jupyter

# Tini: support jupyter running
ENV TINI_VERSION v0.8.4
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

# Flask: web-container
RUN pip install flask

# MongoDB: NoSQL database
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 && \
    echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list && \
    sudo apt-get update
RUN apt-get install -y mongodb-org
RUN pip install pymongo

# docker-py: python interface to interact with docker
RUN pip install docker-py

# expose 80 (http) and 443 (https) for Nginx, and 5000 for flask, 8888 for jupyter
EXPOSE 80 443 5000 8888

# expose some directories to the host
VOLUME ["/root/dsd", "/etc/nginx/conf.d", "/root/workspace"]

# set workdir to workspace
WORKDIR /root/workspace

# default start jupyter using tini
ENTRYPOINT ["/usr/bin/tini", "--"]
ENV SHELL bash
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888","--no-browser"]
