# This file describes the operating system image to be built.
# See https://docs.docker.com/engine/reference/builder/
# and https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/

# Use Ubuntu 16.04 as our base operating system.
FROM ubuntu:16.04

# Run commands in the following shell.
SHELL ["/bin/bash", "-c"]

# Install necessary commands
RUN apt-get update
RUN apt-get install -y wget \
                       git \
                       net-tools

# Install Go
RUN wget --quiet https://storage.googleapis.com/golang/go1.7.3.linux-amd64.tar.gz
RUN tar -xf go1.7.3.linux-amd64.tar.gz
RUN mv go /usr/local/go

# Build the application
WORKDIR /root
COPY main.go ./
RUN mkdir ./go
RUN export GOPATH=/root/go && \
    export PATH=$PATH:$GOPATH/bin && \
    export PATH=$PATH:/usr/local/go/bin && \
    /usr/local/go/bin/go get -d && \
    /usr/local/go/bin/go build -o myserver main.go
    RUN mv ./myserver /bin/myserver

# Create a non-root user
RUN useradd -m -s /bin/bash myuser
WORKDIR /home/myuser
USER myuser

# Allow the host to access our port 10411
EXPOSE 10411

# Run the server
CMD myserver
