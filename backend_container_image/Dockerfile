FROM node:7-onbuild

# Install Vim as an interactive program to test from xterm
RUN apt-get update && \
    apt-get install -y vim && \
    apt-get install manpages

# Create a non-root user to run the application
RUN useradd -ms /bin/bash me
# RUN echo "me:me" | chpasswd
USER me

EXPOSE 10411

# Run the server
CMD npm start
