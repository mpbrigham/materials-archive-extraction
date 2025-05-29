FROM n8nio/n8n:latest

# Create directories for mounted content
USER root
RUN mkdir -p /home/node/prompts /home/node/email_templates /home/node/specs
RUN chown -R node:node /home/node/prompts /home/node/email_templates /home/node/specs

# Switch back to node user
USER node

# Copy application files
COPY --chown=node:node prompts/ /home/node/prompts/
COPY --chown=node:node email_templates/ /home/node/email_templates/

# Expose the default n8n port
EXPOSE 5678

# Use the default n8n entrypoint
ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
CMD ["n8n"]
