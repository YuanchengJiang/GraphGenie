# Download base image ubuntu 20.04
FROM ubuntu:20.04

# LABEL about the custom image
LABEL maintainer="yuancheng@comp.nus.edu.sg"
LABEL version="0.1"
LABEL description="This is custom Docker Image for the Artifact Evaluation of Paper GraphGenie in ICSE'24."

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN apt update

# Install Dependencies
RUN apt install -y git wget tar python3 python3-pip openjdk-17-jdk libpq-dev vim

RUN pip3 install configparser
RUN pip3 install neo4j
RUN pip3 install redisgraph
RUN pip3 install psycopg2

COPY reproduce.py /reproduce.py

# Get GraphGenie

RUN git clone https://github.com/YuanchengJiang/GraphGenie.git

RUN git clone https://github.com/neo4j-graph-examples/recommendations.git;

RUN wget https://dist.neo4j.org/neo4j-community-5.4.0-unix.tar.gz

RUN tar -xvf neo4j-community-5.4.0-unix.tar.gz

RUN ./neo4j-community-5.4.0/bin/neo4j-admin dbms set-initial-password 12344321

RUN ./neo4j-community-5.4.0/bin/neo4j-admin database load --from-stdin --overwrite-destination=true neo4j < ./recommendations/data/recommendations-50.dump