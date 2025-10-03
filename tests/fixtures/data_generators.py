"""Test data generators for Portainer integration testing."""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid


# ---------------------------
#   Random Data Generators
# ---------------------------
def random_string(length: int = 10) -> str:
    """Generate random string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_hex_string(length: int = 12) -> str:
    """Generate random hex string."""
    return ''.join(random.choices(string.hexdigits.lower(), k=length))


def random_ip_address() -> str:
    """Generate random IP address."""
    return f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def random_port() -> int:
    """Generate random port number."""
    return random.randint(1024, 65535)


def random_timestamp(days_ago: int = 30) -> float:
    """Generate random timestamp within last N days."""
    now = datetime.now()
    random_days = random.randint(0, days_ago)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)

    random_time = now - timedelta(
        days=random_days,
        hours=random_hours,
        minutes=random_minutes,
        seconds=random_seconds
    )
    return random_time.timestamp()


def random_container_id() -> str:
    """Generate random container ID."""
    return random_hex_string(12)


def random_image_id() -> str:
    """Generate random image ID."""
    return f"sha256:{random_hex_string(64)}"


def random_container_name() -> str:
    """Generate random container name."""
    prefixes = ["web", "api", "db", "cache", "app", "service", "worker", "proxy", "monitor"]
    suffixes = ["server", "service", "app", "container", "instance", "node", "cluster"]
    return f"{random.choice(prefixes)}-{random.choice(suffixes)}-{random.randint(1, 99)}"


def random_endpoint_name() -> str:
    """Generate random endpoint name."""
    environments = ["dev", "staging", "prod", "test", "demo"]
    locations = ["us", "eu", "asia", "local", "remote"]
    return f"{random.choice(environments)}-{random.choice(locations)}-{random.randint(1, 9)}"


def random_stack_name() -> str:
    """Generate random stack name."""
    applications = ["web-stack", "api-stack", "data-stack", "monitoring-stack", "logging-stack"]
    return f"{random.choice(applications)}-{random.randint(1, 5)}"


# ---------------------------
#   Container State Generators
# ---------------------------
def random_container_state() -> str:
    """Generate random container state."""
    states = ["running", "exited", "created", "restarting", "paused", "dead"]
    return random.choice(states)


def random_container_status(state: Optional[str] = None) -> str:
    """Generate random container status based on state."""
    state = state or random_container_state()

    status_templates = {
        "running": [
            "Up {hours} hour{s}",
            "Up {minutes} minute{s}",
            "Up {hours} hour{s} {minutes} minute{s}",
            "Up {days} day{s} {hours} hour{s}",
        ],
        "exited": [
            "Exited ({code}) {minutes} minute{s} ago",
            "Exited ({code}) {hours} hour{s} ago",
            "Exited ({code}) {days} day{s} ago",
        ],
        "created": ["Created"],
        "restarting": [
            "Restarting ({seconds} second{s} ago)",
            "Restarting ({minutes} minute{s} ago)",
        ],
        "paused": ["Paused"],
        "dead": ["Dead"],
    }

    templates = status_templates.get(state, ["Unknown"])
    template = random.choice(templates)

    # Fill in placeholders
    if "running" in state:
        hours = random.randint(1, 72)
        minutes = random.randint(1, 59)
        suffix_h = "s" if hours != 1 else ""
        suffix_m = "s" if minutes != 1 else ""
        return template.format(hours=hours, minutes=minutes, s=suffix_h, hours2=hours, minutes2=minutes, s2=suffix_h if hours != 1 else "")
    elif "exited" in state:
        code = random.choice([0, 1, 137, 143])
        minutes = random.randint(1, 59)
        hours = random.randint(1, 24)
        days = random.randint(1, 7)
        suffix = "s" if minutes != 1 else ""
        return template.format(code=code, minutes=minutes, hours=hours, days=days, s=suffix)
    elif "restarting" in state:
        seconds = random.randint(1, 59)
        minutes = random.randint(1, 10)
        suffix = "s" if seconds != 1 else ""
        return template.format(seconds=seconds, minutes=minutes, s=suffix)

    return template


def random_health_status() -> str:
    """Generate random health status."""
    statuses = ["healthy", "unhealthy", "starting", "unknown"]
    return random.choice(statuses)


def random_restart_policy() -> str:
    """Generate random restart policy."""
    policies = ["no", "always", "on-failure", "unless-stopped"]
    return random.choice(policies)


# ---------------------------
#   Port/Network Generators
# ---------------------------
def random_port_config() -> List[Dict[str, Any]]:
    """Generate random port configuration."""
    num_ports = random.randint(0, 3)
    ports = []

    for _ in range(num_ports):
        port_type = random.choice(["tcp", "udp"])
        private_port = random_port()
        public_port = random.choice([None, random_port()])

        port_config = {
            "Type": port_type,
            "PrivatePort": private_port,
        }

        if public_port:
            port_config["PublicPort"] = public_port
            port_config["IP"] = random.choice(["0.0.0.0", "127.0.0.1", ""])
        else:
            port_config["IP"] = "127.0.0.1"

        ports.append(port_config)

    return ports


def random_mount_config() -> List[Dict[str, Any]]:
    """Generate random mount configuration."""
    num_mounts = random.randint(0, 3)
    mounts = []

    mount_types = ["volume", "bind"]
    destinations = ["/data", "/config", "/logs", "/tmp", "/app", "/var/lib/app"]

    for _ in range(num_mounts):
        mount_type = random.choice(mount_types)
        destination = random.choice(destinations)

        if mount_type == "volume":
            source = f"volume_{random_string(8)}"
        else:
            source = f"/host/path/{random_string(6)}"

        mounts.append({
            "Type": mount_type,
            "Source": source,
            "Destination": destination,
            "Mode": random.choice(["rw", "ro"]),
            "RW": mount_type == "volume" and destination in ["/data", "/logs"],
        })

    return mounts


def random_network_config() -> Dict[str, Any]:
    """Generate random network configuration."""
    network_modes = ["bridge", "host", "overlay", "macvlan", "none"]
    network_mode = random.choice(network_modes)

    network = {
        "NetworkMode": network_mode,
        "IPAddress": "unknown" if network_mode == "none" else random_ip_address(),
    }

    if network_mode == "bridge":
        network["Gateway"] = "172.18.0.1"
        network["MacAddress"] = f"02:42:{random_hex_string(2).upper()}:{random_hex_string(2).upper()}:{random_hex_string(2).upper()}"
    elif network_mode == "overlay":
        network["Gateway"] = "10.0.1.1"

    return network


# ---------------------------
#   Label Generators
# ---------------------------
def random_compose_labels() -> Dict[str, str]:
    """Generate random Docker Compose labels."""
    labels = {}

    if random.choice([True, False]):
        labels["com.docker.compose.project"] = f"project-{random_string(8)}"
        labels["com.docker.compose.service"] = random_string(8)
        labels["com.docker.compose.version"] = f"{random.randint(2, 3)}.{random.randint(0, 9)}"

    # Add some random labels
    num_extra_labels = random.randint(0, 3)
    for _ in range(num_extra_labels):
        key = f"project.label.{random_string(5)}"
        value = random_string(10)
        labels[key] = value

    return labels


def random_traefik_labels() -> Dict[str, str]:
    """Generate random Traefik labels."""
    labels = {}

    if random.choice([True, False]):
        labels["traefik.enable"] = "true"
        labels["traefik.http.routers.web.rule"] = f"Host(`{random_string(8)}.example.com`)"
        labels["traefik.http.services.web.loadbalancer.server.port"] = str(random_port())

    return labels


# ---------------------------
#   Complete Entity Generators
# ---------------------------
def generate_random_container(endpoint_id: int = 1, container_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate random container data."""
    if not container_name:
        container_name = random_container_name()

    container_id = random_container_id()
    state = random_container_state()
    base_time = datetime.now()

    # Calculate timestamps based on state
    if state == "running":
        started_at = base_time - timedelta(hours=random.randint(1, 72))
        created_at = started_at - timedelta(hours=random.randint(1, 24))
    elif state == "exited":
        created_at = base_time - timedelta(days=random.randint(1, 30))
        started_at = None
    else:
        created_at = base_time - timedelta(hours=random.randint(1, 24))
        started_at = None

    container = {
        "Id": container_id,
        "Names": [f"/{container_name}"],
        "Image": f"{random_string(8)}:{random.choice(['latest', '1.0', 'v2.1', 'stable'])}",
        "ImageID": random_image_id(),
        "State": state,
        "Status": random_container_status(state),
        "Created": created_at.timestamp(),
        "StartedAt": started_at.isoformat() + "Z" if started_at else None,
        "Ports": random_port_config(),
        "Labels": {},
        "Network": random_network_config(),
        "IPAddress": random_ip_address(),
        "Mounts": random_mount_config(),
        "Compose_Stack": "",
        "Compose_Service": "",
        "Compose_Version": "",
        "Environment": f"endpoint-{endpoint_id}",
        "EndpointId": endpoint_id,
        "ConfigEntryId": "test_portainer_entry_123",
        "ExitCode": 0 if state == "running" else random.choice([0, 1, 137]),
        "Privileged": random.choice([True, False]),
        "_Custom": {
            "Health_Status": random_health_status(),
            "Restart_Policy": random_restart_policy(),
        },
    }

    # Add labels based on random selection
    label_generators = [random_compose_labels, random_traefik_labels]
    for generator in label_generators:
        if random.choice([True, False]):
            labels = generator()
            container["Labels"].update(labels)

    # Extract compose info from labels if present
    if "com.docker.compose.project" in container["Labels"]:
        container["Compose_Stack"] = container["Labels"]["com.docker.compose.project"]
        container["Compose_Service"] = container["Labels"].get("com.docker.compose.service", "")
        container["Compose_Version"] = container["Labels"].get("com.docker.compose.version", "")

    # Format published ports
    ports_list = []
    for port_info in container["Ports"]:
        if "PublicPort" in port_info:
            ip = port_info.get("IP", "0.0.0.0")
            ip_prefix = f"{ip}:" if ip != "0.0.0.0" else ""
            ports_list.append(f'{ip_prefix}{port_info["PublicPort"]}->{port_info["PrivatePort"]}/{port_info["Type"]}')
        elif "PrivatePort" in port_info:
            ports_list.append(f'{port_info["PrivatePort"]}/{port_info["Type"]}')
    container["PublishedPorts"] = ", ".join(ports_list) if ports_list else "none"

    # Format mounts
    mounts_list = []
    for mount_info in container["Mounts"]:
        source = mount_info.get("Source") or mount_info.get("Name")
        destination = mount_info.get("Destination")
        if source and destination:
            mounts_list.append(f"{source}:{destination}")
    container["Mounts"] = ", ".join(mounts_list) if mounts_list else "none"

    return container


def generate_random_endpoint(endpoint_id: int = 1, endpoint_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate random endpoint data."""
    if not endpoint_name:
        endpoint_name = random_endpoint_name()

    endpoint_types = [1, 2, 3]  # Docker, Swarm, Kubernetes
    endpoint_type = random.choice(endpoint_types)

    # Generate container counts based on endpoint type
    if endpoint_type == 1:  # Docker
        total_containers = random.randint(1, 20)
        running = random.randint(1, total_containers)
        stopped = total_containers - running
        healthy = random.randint(0, running)
        unhealthy = running - healthy
    elif endpoint_type == 2:  # Swarm
        total_containers = random.randint(5, 50)
        running = random.randint(3, total_containers)
        stopped = total_containers - running
        healthy = random.randint(0, running)
        unhealthy = running - healthy
    else:  # Kubernetes
        total_containers = random.randint(10, 100)
        running = random.randint(5, total_containers)
        stopped = total_containers - running
        healthy = random.randint(0, running)
        unhealthy = running - healthy

    endpoint = {
        "Id": endpoint_id,
        "Name": endpoint_name,
        "Type": endpoint_type,
        "Status": random.choice([1, 2]),  # 1=Up, 2=Down
        "Snapshots": [
            {
                "DockerVersion": f"{random.randint(20, 25)}.0.{random.randint(0, 9)}",
                "Swarm": endpoint_type == 2,
                "TotalCPU": random.randint(2, 64),
                "TotalMemory": random.randint(4, 128) * 1024 * 1024 * 1024,  # GB to bytes
                "RunningContainerCount": running,
                "StoppedContainerCount": stopped,
                "HealthyContainerCount": healthy,
                "UnhealthyContainerCount": unhealthy,
                "VolumeCount": random.randint(0, 50),
                "ImageCount": random.randint(5, 200),
                "ServiceCount": random.randint(0, 20) if endpoint_type in [2, 3] else 0,
                "StackCount": random.randint(0, 15),
            }
        ],
    }

    return endpoint


def generate_random_stack(endpoint_id: int = 1, stack_name: Optional[str] = None) -> Dict[str, Any]:
    """Generate random stack data."""
    if not stack_name:
        stack_name = random_stack_name()

    stack_types = [1, 2, 3]  # Compose, Swarm, Kubernetes
    stack_type = random.choice(stack_types)

    # Adjust stack type based on endpoint if specified
    if endpoint_id == 2 and stack_type == 1:
        stack_type = 2  # Force Swarm for swarm endpoint
    elif endpoint_id == 3 and stack_type in [1, 2]:
        stack_type = 3  # Force Kubernetes for k8s endpoint

    stack = {
        "Id": random.randint(1, 1000),
        "Name": stack_name,
        "Type": stack_type,
        "Status": random.choice([1, 2]),  # 1=Active, 2=Inactive
        "EndpointId": endpoint_id,
        "ConfigEntryId": "test_portainer_entry_123",
    }

    return stack


# ---------------------------
#   Batch Generators
# ---------------------------
def generate_random_containers(count: int, endpoint_id: int = 1) -> List[Dict[str, Any]]:
    """Generate multiple random containers."""
    containers = []
    for i in range(count):
        container = generate_random_container(endpoint_id, f"container-{i + 1}")
        containers.append(container)
    return containers


def generate_random_endpoints(count: int) -> List[Dict[str, Any]]:
    """Generate multiple random endpoints."""
    endpoints = []
    for i in range(count):
        endpoint = generate_random_endpoint(i + 1, f"endpoint-{i + 1}")
        endpoints.append(endpoint)
    return endpoints


def generate_random_stacks(count: int, endpoint_id: int = 1) -> List[Dict[str, Any]]:
    """Generate multiple random stacks."""
    stacks = []
    for i in range(count):
        stack = generate_random_stack(endpoint_id, f"stack-{i + 1}")
        stacks.append(stack)
    return stacks


# ---------------------------
#   Edge Case Generators
# ---------------------------
def generate_container_edge_cases() -> List[Dict[str, Any]]:
    """Generate containers with edge cases."""
    base_time = datetime.now()

    edge_cases = [
        # Container with very long name
        {
            "Id": random_container_id(),
            "Names": [f"/{'very-long-container-name-' * 3}"],
            "Image": "nginx:latest",
            "State": "running",
            "Status": "Up 1 hour",
            "Created": (base_time - timedelta(hours=2)).timestamp(),
            "Ports": [],
            "Labels": {},
        },
        # Container with special characters in name
        {
            "Id": random_container_id(),
            "Names": ["/test_container.with-dashes_and_underscores"],
            "Image": "nginx:latest",
            "State": "running",
            "Status": "Up 30 minutes",
            "Created": (base_time - timedelta(hours=1)).timestamp(),
            "Ports": [],
            "Labels": {},
        },
        # Container with no ports
        {
            "Id": random_container_id(),
            "Names": ["/no-ports-container"],
            "Image": "alpine:latest",
            "State": "running",
            "Status": "Up 15 minutes",
            "Created": (base_time - timedelta(minutes=30)).timestamp(),
            "Ports": [],
            "Labels": {},
        },
        # Container with many ports
        {
            "Id": random_container_id(),
            "Names": ["/many-ports-container"],
            "Image": "multi-port-app:latest",
            "State": "running",
            "Status": "Up 45 minutes",
            "Created": (base_time - timedelta(hours=1)).timestamp(),
            "Ports": [
                {"IP": "0.0.0.0", "PrivatePort": p, "PublicPort": p, "Type": "tcp"}
                for p in range(8080, 8090)
            ],
            "Labels": {},
        },
        # Container with no labels
        {
            "Id": random_container_id(),
            "Names": ["/no-labels-container"],
            "Image": "ubuntu:latest",
            "State": "exited",
            "Status": "Exited (0) 1 hour ago",
            "Created": (base_time - timedelta(hours=2)).timestamp(),
            "Ports": [],
            "Labels": {},
        },
    ]

    return edge_cases


def generate_endpoint_edge_cases() -> List[Dict[str, Any]]:
    """Generate endpoints with edge cases."""
    edge_cases = [
        # Endpoint with minimal resources
        {
            "Id": 999,
            "Name": "minimal-endpoint",
            "Type": 1,
            "Status": 1,
            "Snapshots": [
                {
                    "DockerVersion": "20.10.0",
                    "Swarm": False,
                    "TotalCPU": 1,
                    "TotalMemory": 1024 * 1024 * 1024,  # 1GB
                    "RunningContainerCount": 0,
                    "StoppedContainerCount": 0,
                    "HealthyContainerCount": 0,
                    "UnhealthyContainerCount": 0,
                    "VolumeCount": 0,
                    "ImageCount": 1,
                    "ServiceCount": 0,
                    "StackCount": 0,
                }
            ],
        },
        # Endpoint with maximum resources
        {
            "Id": 998,
            "Name": "maximal-endpoint",
            "Type": 3,
            "Status": 1,
            "Snapshots": [
                {
                    "DockerVersion": "25.0.0",
                    "Swarm": False,
                    "TotalCPU": 256,
                    "TotalMemory": 1024 * 1024 * 1024 * 1024,  # 1TB
                    "RunningContainerCount": 1000,
                    "StoppedContainerCount": 500,
                    "HealthyContainerCount": 800,
                    "UnhealthyContainerCount": 200,
                    "VolumeCount": 1000,
                    "ImageCount": 5000,
                    "ServiceCount": 100,
                    "StackCount": 200,
                }
            ],
        },
    ]

    return edge_cases


# ---------------------------
#   Scenario Generators
# ---------------------------
def generate_scenario_all_running(endpoint_id: int = 1, count: int = 5) -> List[Dict[str, Any]]:
    """Generate scenario where all containers are running."""
    containers = []
    for i in range(count):
        container = generate_random_container(endpoint_id, f"running-app-{i + 1}")
        container["State"] = "running"
        container["Status"] = f"Up {random.randint(1, 24)} hours"
        container["_Custom"]["Health_Status"] = "healthy"
        containers.append(container)
    return containers


def generate_scenario_all_stopped(endpoint_id: int = 1, count: int = 5) -> List[Dict[str, Any]]:
    """Generate scenario where all containers are stopped."""
    containers = []
    for i in range(count):
        container = generate_random_container(endpoint_id, f"stopped-app-{i + 1}")
        container["State"] = "exited"
        container["Status"] = f"Exited (0) {random.randint(1, 24)} hours ago"
        container["_Custom"]["Health_Status"] = "unknown"
        containers.append(container)
    return containers


def generate_scenario_mixed_health(endpoint_id: int = 1, count: int = 10) -> List[Dict[str, Any]]:
    """Generate scenario with mixed health statuses."""
    containers = []
    health_statuses = ["healthy", "unhealthy", "starting", "unknown"]

    for i in range(count):
        container = generate_random_container(endpoint_id, f"mixed-health-app-{i + 1}")
        container["State"] = "running"
        container["_Custom"]["Health_Status"] = random.choice(health_statuses)
        containers.append(container)
    return containers


def generate_scenario_compose_stack(endpoint_id: int = 1) -> Dict[str, Any]:
    """Generate a complete compose stack scenario."""
    stack_name = "test-compose-stack"
    services = ["web", "api", "db", "cache", "worker"]

    containers = {}
    for service in services:
        container = generate_random_container(endpoint_id, f"{stack_name}_{service}")
        container["Labels"] = {
            "com.docker.compose.project": stack_name,
            "com.docker.compose.service": service,
            "com.docker.compose.version": "3.8",
        }
        container["Compose_Stack"] = stack_name
        container["Compose_Service"] = service
        container["Compose_Version"] = "3.8"
        containers[f"{endpoint_id}_{stack_name}_{service}"] = container

    return {
        "containers": containers,
        "stack": {
            "Id": 1,
            "Name": stack_name,
            "Type": 1,
            "Status": 1,
            "EndpointId": endpoint_id,
            "ConfigEntryId": "test_portainer_entry_123",
        }
    }


# ---------------------------
#   Helper Functions
# ---------------------------
def create_test_scenario(name: str, **kwargs) -> Dict[str, Any]:
    """Create a test scenario with specific parameters."""
    scenarios = {
        "single_container": lambda: {
            "endpoints": {1: generate_random_endpoint(1)},
            "containers": {f"1_{random_container_name()}": generate_random_container(1)},
            "stacks": {},
        },
        "multiple_endpoints": lambda: {
            "endpoints": {i + 1: generate_random_endpoint(i + 1) for i in range(kwargs.get("count", 3))},
            "containers": {},
            "stacks": {},
        },
        "full_environment": lambda: {
            "endpoints": {i + 1: generate_random_endpoint(i + 1) for i in range(3)},
            "containers": {},
            "stacks": {i + 1: generate_random_stack(i + 1) for i in range(5)},
        },
    }

    generator = scenarios.get(name)
    if generator:
        return generator()
    else:
        raise ValueError(f"Unknown scenario: {name}")


def randomize_existing_data(data: Dict[str, Any], randomization_level: float = 0.1) -> Dict[str, Any]:
    """Randomize existing data for testing variations."""
    if not isinstance(data, dict):
        return data

    randomized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            randomized[key] = randomize_existing_data(value, randomization_level)
        elif isinstance(value, list):
            randomized[key] = [
                randomize_existing_data(item, randomization_level) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str) and random.random() < randomization_level:
            randomized[key] = random_string(len(value)) if len(value) > 0 else value
        elif isinstance(value, (int, float)) and random.random() < randomization_level:
            randomized[key] = value + random.randint(-10, 10)
        else:
            randomized[key] = value

    return randomized
