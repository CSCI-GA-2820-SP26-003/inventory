# This image has selenium and chrome driver already installed
FROM quay.io/rofrano/pipeline-selenium:sp26

ARG USERNAME=vscode
USER root

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev

COPY config/insecure-registry.json /etc/docker/daemon.json 
USER $USERNAME
# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
