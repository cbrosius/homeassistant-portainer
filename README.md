# Portainer integration for Home Assistant
(based on the work of [@tomaae](https://github.com/tomaae/homeassistant-portainer))

![GitHub release (latest by date)](https://img.shields.io/github/v/release/cbrosius/homeassistant-portainer?style=plastic)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=plastic)](https://github.com/hacs/integration)
![Project Stage](https://img.shields.io/badge/project%20stage-development-yellow.svg?style=plastic)
![GitHub all releases](https://img.shields.io/github/downloads/cbrosius/homeassistant-portainer/total?style=plastic)

![GitHub commits since latest release](https://img.shields.io/github/commits-since/cbrosius/homeassistant-portainer/latest?style=plastic)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/cbrosius/homeassistant-portainer?style=plastic)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/cbrosius/homeassistant-portainer/ci.yml?style=plastic)

![Portainer Logo](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/logo.png)


Monitor and control Portainer from Home Assistant.

Features:
* Get Portainer-Endpoints and create a device for each endpoint
* Get Containers per Endpoint and create a device for each container
    * provide buttons to control containers
    * provide sensors to monitor container status
    * provide sensors to monitor container details
    * set the 'Connected via' Attribute in the devices to handle dependencies correct
* Get Stacks per Endpoint and create a device for each stack
    * provide buttons to control stacks
    * provide sensors to monitor stack status
    * provide sensors to monitor stack details


# Features
## Endpoints
For each endpoint configured in Portainer, a dedicated Home Assistant device is created. This device represents the Portainer endpoint itself and acts as a parent for all container devices running on it.

The endpoint device provides key details and sensors, including:
*   **Details**: Endpoint name, Docker version, and a direct link to its configuration URL in Portainer.
*   **Sensors**:
    *   Reachability status
    *   Counts for unhealthy and stopped containers
    *   Totals for images, volumes, and stacks

![Endpoints](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/endpoints.png)

## Containers
For each container managed by a Portainer endpoint, a corresponding Home Assistant device is created. This device is automatically linked to its parent endpoint device, making it easy to see which containers belong to which environment.

The container device provides a central place to monitor its status and details. Key information and controls include:

*   **State Sensor**: The primary sensor shows the container's current state (e.g., `running`, `stopped`, `exited`). For running containers with a health check, the state will be more descriptive (e.g., `running (healthy)`).
*   **Detail Sensors**: Additional sensors are created to provide more granular information, such as:
     *   IP Address
     *   Published Ports
     *   Image ID
     *   Start Time and Creation Date
     *   Compose Stack and Service names (if applicable)
     *   Health Status (enabled by default)
     *   Restart Policy (enabled by default)
*   **Controls**: You can control the container directly from Home Assistant using the `portainer.perform_container_action` service. This allows you to `start`, `stop`, `restart`, or `kill` one or more containers, which is perfect for automations and scripts.

![Containers](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/containers.png)

## Stacks
For each stack defined in a Portainer endpoint, a corresponding Home Assistant device is created. This device is linked to its parent endpoint device.

The stack device provides sensors to monitor its status and composition. Key information includes:
*   **State Sensor**: The primary sensor shows the stack's current state (e.g., `active`, `inactive`, `limited`).
*   **Detail Sensors**:
    *   Container Count: The number of containers running as part of this stack.
*   **Controls**: You can manage the stack directly from Home Assistant using the `portainer.perform_stack_action` service. This allows you to `start`, `stop` the entire stack.

![Stacks](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/stacks.png)

# Services
The Portainer integration exposes services to allow direct control over your containers and stacks from Home Assistant automations and scripts.

## `portainer.perform_container_action`
This service allows you to perform actions like starting, stopping, restarting, or killing one or more containers managed by your Portainer instance.

### Service Data Attributes:
*   **`action`** (Required): The action to perform.
    *   Possible values: `start`, `stop`, `restart`, `kill`
*   **`container_devices`** (Required): A list of Home Assistant device IDs corresponding to the containers you wish to control.

### Example Usage:
To use this service, you'll need the Home Assistant `device_id` of the container(s) you want to control. You can find this by navigating to the device page in Home Assistant (Settings -> Devices & Services -> Devices, then select your container device) or by inspecting the device in Developer Tools -> States.

Here's an example of how to stop a specific container using this service in a Home Assistant automation or script:

```yaml
service: portainer.perform_container_action
data:
  action: stop
  container_devices:
    - device_id: a0e2c2f2e7b1a4d5c6f7e8d9c0b1a2c3 # Replace with your container's device_id
```

As an alternative, you can use the UI to perform this action.

![Perform Container Action](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/container_action.png)

## `portainer.perform_stack_action`
This service allows you to perform actions on an entire stack, such as starting or stopping all containers within it.

### Service Data Attributes:
*   **`action`** (Required): The action to perform.
    *   Possible values: `start`, `stop`
*   **`stack_devices`** (Required): A list of Home Assistant device IDs corresponding to the stacks you wish to control.

### Example Usage:
To use this service, you'll need the Home Assistant `device_id` of the stack(s) you want to control. You can find this by navigating to the device page in Home Assistant (Settings -> Devices & Services -> Devices, then select your stack device) or by inspecting the device in Developer Tools -> States.

Here's an example of how to stop a specific stack using this service in a Home Assistant automation or script:

```yaml
service: portainer.perform_stack_action
data:
  action: stop
  stack_devices:
    - device_id: b1f3d3a3f8c2b5e6d7a8b9c0d1e2f3a4 # Replace with your stack's device_id
```

As an alternative, you can use the UI to perform this action.

![Perform Stack Action](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/stack_action.png)

## `portainer.recreate_container`
This service allows you to recreate a container, which stops the container, removes it, and starts a new one with the same configuration. Optionally pulls the latest image before recreating.

### Service Data Attributes:
*   **`container_devices`** (Required): A list of Home Assistant device IDs corresponding to the containers you wish to recreate.
*   **`pull_image`** (Optional): Whether to pull the latest image before recreating the container. Defaults to `true`.

### Example Usage:
To recreate a specific container using this service in a Home Assistant automation or script:

```yaml
service: portainer.recreate_container
data:
  container_devices:
    - device_id: a0e2c2f2e7b1a4d5c6f7e8d9c0b1a2c3 # Replace with your container's device_id
  pull_image: true
```

As an alternative, you can use the UI to perform this action.


# Install integration
This integration is available via the Home Assistant Community Store ([HACS](https://hacs.xyz/)).

Since this integration is not in the default HACS repository, you must add it as a custom repository.

1.  **Navigate to HACS**: In Home Assistant, go to `HACS` > `Integrations`.
2.  **Add Custom Repository**: Click the three-dots menu in the top-right corner and select `Custom repositories`.
3.  **Add the Repository URL**:
    *   In the `Repository` field, paste this GitHub repository's URL: `https://github.com/cbrosius/homeassistant-portainer`
    *   In the `Category` dropdown, select `Integration`.
    *   Click `Add`.
4.  **Install the Integration**: The "Portainer" integration will now appear in your HACS integrations list. Click `Install` and proceed with the installation.
5.  **Restart Home Assistant**: After the installation is complete, you must restart Home Assistant for the integration to be loaded.

After restarting, you can proceed with getting your access token and setting up the integration.

## Get portainer access token
1. Login into your portainer instance
2. Click you username at top right and select "My Account"
3. Under "Access tokens", click "Add access token"
4. Enter name for your access token (can be anything, for example "homeassistant")
5. Copy displayed access token for use in integration setup

## Setup integration
Setup this integration for your Portainer in Home Assistant via `Configuration -> Integrations -> Add -> Portainer`.
You can add this integration several times for different portainer instances.

The setup process includes the following steps:

1. **Initial Configuration**: Enter your Portainer instance details
   * "Name of the integration" - Friendly name for this Portainer instance
   * "Host" - Use hostname or IP and port (example: portainer.domain.tld or 192.168.0.2:9000)
   * "Access token" - Use access token from previous step
   * "Use SSL" - Connect to portainer using SSL
   * "Verify SSL certificate" - Validate SSL certificate (must be trusted certificate)

2. **Endpoint Selection**: Choose which Portainer endpoints to monitor

3. **Container & Stack Selection**: Select specific containers and stacks to track

All features (health check sensors, restart policy sensors, and action buttons) are automatically enabled for the best experience. No additional configuration steps are required.

## Configuration
The integration automatically enables all features by default for the best user experience:

* **Health Check Sensors** - Monitor container health status from Docker health checks
* **Restart Policy Sensors** - Display container restart policies
* **Action Buttons** - Provide start/stop/restart/kill buttons for containers and stacks

No additional configuration is required - all features are enabled automatically. If you need to modify endpoint, container, or stack selections, use `Configuration -> Integrations -> Portainer -> Configure`.

![Configuration](https://raw.githubusercontent.com/cbrosius/homeassistant-portainer/master/docs/assets/images/ui/options.png)

## Advanced Features

### Smart Repair Issue Management
The integration includes intelligent repair issue management to prevent false positives during container startup:

* **Consecutive Failure Tracking**: Repair issues are only created after 3 consecutive failures
* **Automatic Recovery**: When devices are found again, failure counters are cleared and issues are automatically resolved
* **Startup Safety**: Temporary API unavailability during container startup won't trigger repair issues

This ensures you only see repair issues for genuine persistent problems, not temporary startup conditions.

### Health Status Intelligence
* **Multi-State Support**: Health sensors show `healthy`, `unhealthy`, `starting`, or `unavailable` states
* **Container State Awareness**: Non-running containers show `unavailable` health status (since health checks don't apply)
* **Docker Integration**: Pulls health status directly from Docker's health check system

## Troubleshooting

### Common Issues

**Containers not appearing in Home Assistant:**
* Verify the container is selected during integration setup
* Check that the Portainer endpoint is reachable and has status "Up"
* Review Home Assistant logs for connection errors

**Health status showing "unknown":**
* Ensure the container has Docker health checks configured
* Check that the container is in "running" state
* Verify Portainer API connectivity

**Repair issues appearing:**
* These only appear after 3 consecutive failures (not temporary issues)
* Check Portainer server connectivity
* Verify container/endpoints still exist in Portainer

**Action buttons not working:**
* Ensure the integration has action buttons enabled (default: enabled)
* Check that the target container/endpoint is reachable
* Verify user permissions in Portainer

### Debug Logging
To enable debug logging for troubleshooting, add the following to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.portainer: debug
```

### Getting Help
* Check the [GitHub Issues](https://github.com/cbrosius/homeassistant-portainer/issues) page for known issues
* Enable debug logging and check Home Assistant logs for detailed error messages
* Verify your Portainer instance is accessible and your access token is valid
