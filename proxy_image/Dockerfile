FROM node:4-onbuild

# Install net-tools so the server can get the IP of our host
RUN apt-get update && \
    apt-get install -y net-tools

EXPOSE 10412

# Run the server
CMD npm start
