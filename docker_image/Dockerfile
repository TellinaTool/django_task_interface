FROM ubuntu:16.04

SHELL ["/bin/bash", "-c"]

RUN apt-get update
RUN apt-get install -y wget
RUN wget --quiet https://storage.googleapis.com/golang/go1.7.3.linux-amd64.tar.gz
RUN tar -xf go1.7.3.linux-amd64.tar.gz
RUN mv go /usr/local/go

RUN apt-get update
RUN apt-get install -y git

RUN apt-get update
RUN apt-get install -y net-tools

RUN apt-get update
RUN apt-get install -y curl

RUN useradd -m -s /bin/bash myuser
COPY main.go /home/myuser
RUN chown myuser /home/myuser/main.go

USER myuser
WORKDIR /home/myuser

RUN mkdir go
RUN export GOPATH=~/go && \
    export PATH=$PATH:$GOPATH/bin && \
    export PATH=$PATH:/usr/local/go/bin && \
    /usr/local/go/bin/go get -d && \
    /usr/local/go/bin/go build -o myserver main.go
USER root
RUN mv /home/myuser/myserver /bin/myserver
USER myuser
WORKDIR /home/myuser

EXPOSE 10411

CMD myserver
