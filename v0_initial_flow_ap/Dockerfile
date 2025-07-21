FROM activepieces/activepieces:latest
USER root

# Install Python, pip, and required Python packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && pip3 install requests

# Install Node.js package for Gemini AI
RUN npm install -g @google/generative-ai
