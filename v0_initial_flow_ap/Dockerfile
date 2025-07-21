FROM activepieces/activepieces:latest
USER root

# Only install the requests package since Python/pip already exist
RUN pip install requests

# Install Node.js package for Gemini AI
RUN npm install -g @google/generative-ai
