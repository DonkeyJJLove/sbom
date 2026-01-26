FROM jenkins/jenkins:lts

USER root

# Bazowe narzędzia potrzebne w pipeline (curl + jq + git + bash) + klucze do repo Dockera
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg jq git bash coreutils \
 && rm -rf /var/lib/apt/lists/*

# docker cli (żeby pipeline mógł robić docker run)
RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" \
      > /etc/apt/sources.list.d/docker.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends docker-ce-cli; \
    rm -rf /var/lib/apt/lists/*

USER jenkins
