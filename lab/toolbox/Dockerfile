FROM debian:12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl jq git bash coreutils \
 && rm -rf /var/lib/apt/lists/*

# Syft
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
  | sh -s -- -b /usr/local/bin

# Grype
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \
  | sh -s -- -b /usr/local/bin

WORKDIR /repo

CMD ["bash","-lc","sleep infinity"]
