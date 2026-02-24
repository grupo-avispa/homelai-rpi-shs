# Use slim Python base image
FROM python:3.12-slim

# Install git
RUN apt-get update && apt-get install -y git \
    && apt autoclean -y \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install uv (dependency manager)
RUN pip install uv

# Clone the other repo
RUN git clone https://github.com/opfernandez/diet_classifier_pytorch.git /SHS/diet_classifier_pytorch

WORKDIR /SHS

# Copy the homelai package into the container
COPY . /SHS/homelai-rpi-shs

# Sync dependencies from both pyprojects into the same environment
WORKDIR /SHS/homelai-rpi-shs
RUN uv sync
WORKDIR /SHS/diet_classifier_pytorch
RUN uv sync

# Set the working directory to the homelai package
WORKDIR /SHS/

# Start a bash shell by default
CMD ["bash"]