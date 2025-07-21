FROM activepieces/activepieces:latest
USER root

# Install pip and requests (python3 already exists in base image)
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install requests

# Install Node.js package for Gemini AI
RUN npm install -g @google/generative-ai
