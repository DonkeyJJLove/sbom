FROM debian:12-slim

# Minimal toolchain + TLS root CAs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl jq git bash coreutils \
 && rm -rf /var/lib/apt/lists/*

# Optional: pin versions (leave empty to install latest)
ARG SYFT_VERSION=
ARG GRYPE_VERSION=

# Syft
RUN set -eux; \
  if [ -n "$SYFT_VERSION" ]; then \
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
      | sh -s -- -b /usr/local/bin "v${SYFT_VERSION}"; \
  else \
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
      | sh -s -- -b /usr/local/bin; \
  fi; \
  syft version

# Grype
RUN set -eux; \
  if [ -n "$GRYPE_VERSION" ]; then \
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \
      | sh -s -- -b /usr/local/bin "v${GRYPE_VERSION}"; \
  else \
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \
      | sh -s -- -b /usr/local/bin; \
  fi; \
  grype version

# Sensowne domyślne wartości, żeby pipeline nie padał gdy Jenkins nie przekaże env
# (u Ciebie to dokładnie rozwiązuje "Unknown TARGET_KIND=")
ENV TARGET_KIND=repo \
    TARGET_REF=.

WORKDIR /repo

# Standardowo: kontener jako toolbox-interactive/daemon
CMD ["bash","-lc","sleep infinity"]
