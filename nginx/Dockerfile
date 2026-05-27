FROM nginx:stable

# Copy the custom nginx vhost configuration
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Simple healthcheck to let orchestrators know the proxy is up
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1/api/v1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
