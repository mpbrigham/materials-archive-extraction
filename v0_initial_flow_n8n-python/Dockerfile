FROM n8nio/n8n:latest

USER root

# Install Python and essential packages
RUN apk add --update --no-cache \
    python3 \
    py3-pip \
    py3-numpy \
    py3-pandas && \
    python3 -m pip install --upgrade pip && \
    pip3 install --no-cache-dir \
        google-generativeai \
        pypdf2 \
        pdfplumber \
        python-magic

USER node
