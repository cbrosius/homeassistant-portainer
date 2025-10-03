#!/usr/bin/env bash
source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)
# Copyright (c) 2021-2025 tteck
# Author: tteck (tteckster)
# License: MIT | https://github.com/community-scripts/ProxmoxVE/raw/main/LICENSE
# Source: https://www.docker.com/

APP="Docker"
var_tags="${var_tags:-docker}"
var_cpu="${var_cpu:-2}"
var_ram="${var_ram:-2048}"
var_disk="${var_disk:-4}"
var_os="${var_os:-debian}"
var_version="${var_version:-12}"
var_unprivileged="${var_unprivileged:-1}"

header_info "$APP"
variables
color
catch_errors

function update_script() {
  header_info
  check_container_storage
  check_container_resources

  get_latest_release() {
    curl -fsSL https://api.github.com/repos/"$1"/releases/latest | grep '"tag_name":' | cut -d'"' -f4
  }

  msg_info "Updating base system"
  $STD apt-get update
  $STD apt-get -y upgrade
  msg_ok "Base system updated"

  msg_info "Updating Docker Engine"
  $STD apt-get install --only-upgrade -y docker-ce docker-ce-cli containerd.io
  msg_ok "Docker Engine updated"

  if [[ -f /usr/local/lib/docker/cli-plugins/docker-compose ]]; then
    COMPOSE_BIN="/usr/local/lib/docker/cli-plugins/docker-compose"
    COMPOSE_NEW_VERSION=$(get_latest_release "docker/compose")
    msg_info "Updating Docker Compose to $COMPOSE_NEW_VERSION"
    curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_NEW_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
      -o "$COMPOSE_BIN"
    chmod +x "$COMPOSE_BIN"
    msg_ok "Docker Compose updated"
  fi

  if docker ps -a --format '{{.Names}}' | grep -q '^portainer$'; then
    msg_info "Updating Portainer"
    $STD docker pull portainer/portainer-ce:latest
    $STD docker stop portainer && docker rm portainer
    $STD docker volume create portainer_data >/dev/null 2>&1
    $STD docker run -d \
      -p 8000:8000 \
      -p 9443:9443 \
      --name=portainer \
      --restart=always \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v portainer_data:/data \
      portainer/portainer-ce:latest
    msg_ok "Updated Portainer"
  fi

  if docker ps -a --format '{{.Names}}' | grep -q '^portainer_agent$'; then
    msg_info "Updating Portainer Agent"
    $STD docker pull portainer/agent:latest
    $STD docker stop portainer_agent && docker rm portainer_agent
    $STD docker run -d \
      -p 9001:9001 \
      --name=portainer_agent \
      --restart=always \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v /var/lib/docker/volumes:/var/lib/docker/volumes \
      portainer/agent
    msg_ok "Updated Portainer Agent"
  fi

  msg_info "Cleaning up"
  $STD apt-get -y autoremove
  $STD apt-get -y autoclean
  msg_ok "Cleanup complete"
  exit
}

start
build_container
description

# Extension: Create Home Assistant Dev Container with SSH for VS Code Remote

msg_info "Creating Home Assistant Dev Container for remote development"

# Check if the container already exists, remove if yes
if docker ps -a --format '{{.Names}}' | grep -q '^homeassistant-dev$'; then
  msg_info "Removing existing homeassistant-dev container"
  $STD docker stop homeassistant-dev
  $STD docker rm homeassistant-dev
fi

# Create Home Assistant Dev container
$STD docker run -d \
  --name homeassistant-dev \
  --restart unless-stopped \
  -p 8123:8123 \     # Home Assistant UI
  -p 2222:22 \       # SSH access for VS Code Remote
  -p 3000:3000 \     # Example port for dev tools / VS Code extensions
  -v homeassistant_config:/config \  # Persistent configuration
  --privileged \     # Full device access if needed
  ghcr.io/home-assistant/home-assistant:stable

msg_ok "Home Assistant Dev container created and started"

msg_info "Installing and configuring SSH server inside the container for VS Code Remote access"
$STD docker exec -it homeassistant-dev bash -c "\
  apt-get update && apt-get install -y openssh-server; \
  mkdir -p /var/run/sshd; \
  echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config; \
  sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config; \
  sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config; \
  service ssh restart \
"

# Generate a random root password
random_password=$(docker exec homeassistant-dev openssl rand -base64 12)

msg_info "Setting random root password inside Home Assistant Dev container"
$STD docker exec homeassistant-dev bash -c "echo 'root:${random_password}' | chpasswd"

msg_ok "Random root password set"

echo -e "${INFO} Home Assistant Dev container is running."
echo -e "${INFO} Home Assistant UI: http://<YOUR_SERVER_IP>:8123"
echo -e "${INFO} Connect to VS Code Remote SSH on port 2222 with user 'root'"
echo -e "${INFO} One-time root password: ${random_password}"

msg_ok "Completed Successfully!\n"
echo -e "${CREATING}${GN}${APP} setup has been successfully initialized!${CL}"
echo -e "${INFO}${YW} If you installed Portainer, access it at the following URL:${CL}"
echo -e "${TAB}${GATEWAY}${BGN}https://${IP}:9443${CL}"
