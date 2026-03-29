# This image has selenium and chrome driver already installed
FROM quay.io/rofrano/pipeline-selenium:sp26

# Ensure Chromium and chromedriver are installed for BDD tests
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    chromium-driver \
    && sudo rm -rf /var/lib/apt/lists/*

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev

# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
