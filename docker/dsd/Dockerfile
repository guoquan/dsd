FROM ubuntu:14.04
MAINTAINER Guo Quan <guoquan@gmail.com>

ENV REFRESHED_AT 2016-05-06
RUN apt-get update

# Nginx: front-end web server
RUN apt-get install -y nginx

# Python: we are python driven
RUN apt-get install -y python python-pip && \
    pip install -U pip

# Flask: web-container
RUN pip install flask

# MongoDB: NoSQL database
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927 && \
    echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list && \
    sudo apt-get update
RUN apt-get install -y mongodb-org
RUN pip install pymongo

# expose 80 (http) and 443 (https) for Nginx, and 5000 for flask
EXPOSE 80 443 5000

# expose some directories to the host
VOLUME ["/root/workspace", "/etc/nginx" ]

# set workdir to workspace
WORKDIR /root/workspace

# default start bash for development
CMD ["bash"]
