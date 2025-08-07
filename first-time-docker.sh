#!/bin/bash
FEDORA_VERSION=42
set -eou

# Pre-run script to set up docker for the first time
sudo dnf install dnf-plugins-core
sudo dnf config-manager addrepo --from-repofile="https://download.docker.com/linux/fedora/docker-ce.repo" --overwrite
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo groupadd -f docker && sudo gpasswd -a ${USER} docker
sudo usermod -a -G docker $USER
sudo systemctl start docker.service
docker pull fedora:${FEDORA_VERSION}
newgrp docker
