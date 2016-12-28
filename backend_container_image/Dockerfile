FROM node:4-onbuild
# FROM nodesource/trusty:5.1

# Install Vim as an interactive program to test from xterm
RUN apt-get update && \
    apt-get install -y vim

# Create a non-root user to run the application
RUN useradd -m -s /bin/bash myuser
# RUN mkdir /home/myuser
RUN chown 1001:1001 /home/myuser
USER myuser

EXPOSE 10411

# Run the server
CMD npm start
