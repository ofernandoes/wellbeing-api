FROM mcr.microsoft.com/devcontainers/universal:latest
RUN bash -c "$(curl -fsSL https://raw.githubusercontent.com/devcontainers/features/main/src/flutter/install.sh)"
USER vscode
