FROM nodered/node-red:latest

USER root

# Install required npm packages
RUN npm install -g @google/generative-ai && \
    cd /usr/src/node-red && \
    npm install node-red-node-email

USER node-red