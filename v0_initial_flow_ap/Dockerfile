FROM activepieces/activepieces:latest

# Install additional dependencies if needed
USER root

# Install any system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directories for mounted volumes
RUN mkdir -p /root/prompts /root/email_templates /root/schema /root/.activepieces

# Set working directory
WORKDIR /root

# Switch back to default user
USER 1000

# Expose the default ActivePieces port
EXPOSE 8080

# Start ActivePieces
CMD ["npm", "start"]
