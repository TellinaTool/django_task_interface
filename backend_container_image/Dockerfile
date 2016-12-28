FROM node:4-onbuild

# Install Vim as an interactive program to test from xterm
RUN apt-get update && \
    apt-get install -y vim

# Create a non-root user to run the application
RUN useradd -m -s /bin/bash study_participant
USER study_participant

EXPOSE 10411

# Run the server
CMD npm start
