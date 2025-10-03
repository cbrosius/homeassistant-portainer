"""Entity data fixtures for Portainer integration testing."""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import random


# ---------------------------
#   Endpoint Entity Data Fixtures
# ---------------------------
def get_endpoint_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get processed endpoint entity data."""
    base_time = datetime.now()
    return {
        1: {
            "Id": 1,
            "Name": "local",
            "Type": 1,
            "Status": 1,
            "DockerVersion": "24.0.6",
            "Swarm": False,
            "TotalCPU": 8,
            "TotalMemory": 16777216000,  # 16GB
            "RunningContainerCount": 5,
            "StoppedContainerCount": 2,
            "HealthyContainerCount": 4,
            "UnhealthyContainerCount": 1,
            "VolumeCount": 12,
            "ImageCount": 25,
            "ServiceCount": 0,
            "StackCount": 3,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        2: {
            "Id": 2,
            "Name": "swarm-cluster",
            "Type": 2,
            "Status": 1,
            "DockerVersion": "23.0.3",
            "Swarm": True,
            "TotalCPU": 16,
            "TotalMemory": 33554432000,  # 32GB
            "RunningContainerCount": 8,
            "StoppedContainerCount": 1,
            "HealthyContainerCount": 7,
            "UnhealthyContainerCount": 1,
            "VolumeCount": 20,
            "ImageCount": 45,
            "ServiceCount": 5,
            "StackCount": 6,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        3: {
            "Id": 3,
            "Name": "kubernetes-cluster",
            "Type": 3,
            "Status": 1,
            "DockerVersion": "25.0.0",
            "Swarm": False,
            "TotalCPU": 32,
            "TotalMemory": 67108864000,  # 64GB
            "RunningContainerCount": 15,
            "StoppedContainerCount": 3,
            "HealthyContainerCount": 12,
            "UnhealthyContainerCount": 3,
            "VolumeCount": 30,
            "ImageCount": 80,
            "ServiceCount": 12,
            "StackCount": 8,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        4: {
            "Id": 4,
            "Name": "offline-endpoint",
            "Type": 1,
            "Status": 2,  # Down
            "DockerVersion": "Unknown",
            "Swarm": False,
            "TotalCPU": 0,
            "TotalMemory": 0,
            "RunningContainerCount": 0,
            "StoppedContainerCount": 0,
            "HealthyContainerCount": 0,
            "UnhealthyContainerCount": 0,
            "VolumeCount": 0,
            "ImageCount": 0,
            "ServiceCount": 0,
            "StackCount": 0,
            "ConfigEntryId": "test_portainer_entry_123",
        },
    }


def get_endpoint_entity_data_empty() -> Dict[str, Dict[str, Any]]:
    """Get empty endpoint entity data."""
    return {}


def get_endpoint_entity_data_single() -> Dict[str, Dict[str, Any]]:
    """Get single endpoint entity data."""
    return {
        1: {
            "Id": 1,
            "Name": "local",
            "Type": 1,
            "Status": 1,
            "DockerVersion": "24.0.6",
            "Swarm": False,
            "TotalCPU": 4,
            "TotalMemory": 8589934592,  # 8GB
            "RunningContainerCount": 3,
            "StoppedContainerCount": 1,
            "HealthyContainerCount": 2,
            "UnhealthyContainerCount": 1,
            "VolumeCount": 5,
            "ImageCount": 10,
            "ServiceCount": 0,
            "StackCount": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        }
    }


# ---------------------------
#   Container Entity Data Fixtures
# ---------------------------
def get_container_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get processed container entity data."""
    base_time = datetime.now()
    return {
        "1_web-server": {
            "Id": "abc123def456",
            "Name": "web-server",
            "Names": ["/web-server"],
            "Image": "nginx:latest",
            "ImageID": "sha256:nginx_latest_1234567890abcdef",
            "State": "running",
            "Status": "Up 2 hours",
            "Created": (base_time - timedelta(hours=24)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=2)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.10",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 80,
                    "PublicPort": 8080,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "8080->80/tcp",
            "Mounts": "none",
            "Compose_Stack": "web-stack",
            "Compose_Service": "web",
            "Compose_Version": "3.8",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "unless-stopped",
            },
        },
        "1_database": {
            "Id": "def789ghi012",
            "Name": "database",
            "Names": ["/database"],
            "Image": "postgres:15",
            "ImageID": "sha256:postgres_15_abcdef1234567890",
            "State": "running",
            "Status": "Up 30 minutes",
            "Created": (base_time - timedelta(hours=12)).timestamp(),
            "StartedAt": (base_time - timedelta(minutes=30)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.11",
            "Ports": [
                {
                    "IP": "127.0.0.1",
                    "PrivatePort": 5432,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "5432/tcp",
            "Mounts": "/var/lib/docker/volumes/db_data:/var/lib/postgresql/data",
            "Compose_Stack": "web-stack",
            "Compose_Service": "db",
            "Compose_Version": "3.8",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "unless-stopped",
            },
        },
        "1_cache": {
            "Id": "ghi345jkl678",
            "Name": "cache",
            "Names": ["/cache"],
            "Image": "redis:7-alpine",
            "ImageID": "sha256:redis_7_alpine_7890abcdef123456",
            "State": "running",
            "Status": "Up 1 hour",
            "Created": (base_time - timedelta(hours=6)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=1)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.12",
            "Ports": [
                {
                    "PrivatePort": 6379,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "6379/tcp",
            "Mounts": "none",
            "Compose_Stack": "web-stack",
            "Compose_Service": "cache",
            "Compose_Version": "3.8",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "unless-stopped",
            },
        },
        "1_monitoring": {
            "Id": "jkl901mno234",
            "Name": "monitoring",
            "Names": ["/monitoring"],
            "Image": "prometheus:latest",
            "ImageID": "sha256:prometheus_latest_456789abcdef123",
            "State": "running",
            "Status": "Up 45 minutes",
            "Created": (base_time - timedelta(hours=8)).timestamp(),
            "StartedAt": (base_time - timedelta(minutes=45)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.13",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 9090,
                    "PublicPort": 9090,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "9090->9090/tcp",
            "Mounts": "/var/lib/docker/volumes/prometheus_data:/prometheus",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "always",
            },
        },
        "1_backup-service": {
            "Id": "mno567pqr890",
            "Name": "backup-service",
            "Names": ["/backup-service"],
            "Image": "restic/restic",
            "ImageID": "sha256:restic_latest_abcdef1234567890",
            "State": "exited",
            "Status": "Exited (0) 10 minutes ago",
            "Created": (base_time - timedelta(hours=48)).timestamp(),
            "StartedAt": None,
            "Network": "host",
            "IPAddress": "172.18.0.14",
            "Ports": [],
            "PublishedPorts": "none",
            "Mounts": "none",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": True,
            "_Custom": {
                "Health_Status": "unknown",
                "Restart_Policy": "no",
            },
        },
        "1_unhealthy-app": {
            "Id": "pqr123stu456",
            "Name": "unhealthy-app",
            "Names": ["/unhealthy-app"],
            "Image": "myapp:latest",
            "ImageID": "sha256:myapp_latest_123456789abcdef0",
            "State": "running",
            "Status": "Up 5 minutes (unhealthy)",
            "Created": (base_time - timedelta(hours=2)).timestamp(),
            "StartedAt": (base_time - timedelta(minutes=5)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.15",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 3000,
                    "PublicPort": 3000,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "3000->3000/tcp",
            "Mounts": "none",
            "Compose_Stack": "problematic-stack",
            "Compose_Service": "app",
            "Compose_Version": "3.9",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "unhealthy",
                "Restart_Policy": "always",
            },
        },
        "1_legacy-app": {
            "Id": "stu789vwx012",
            "Name": "legacy-app",
            "Names": ["/legacy-app"],
            "Image": "old-app:1.0",
            "ImageID": "sha256:old_app_1_abcdef123456789012",
            "State": "created",
            "Status": "Created",
            "Created": (base_time - timedelta(days=7)).timestamp(),
            "StartedAt": None,
            "Network": "bridge",
            "IPAddress": "unknown",
            "Ports": [],
            "PublishedPorts": "none",
            "Mounts": "none",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": None,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "unknown",
                "Restart_Policy": "no",
            },
        },
    }


def get_container_entity_data_swarm() -> Dict[str, Dict[str, Any]]:
    """Get container entity data for swarm services."""
    base_time = datetime.now()
    return {
        "2_api-gateway": {
            "Id": "swarm123abc456",
            "Name": "api-gateway",
            "Names": ["/api-gateway"],
            "Image": "traefik:v2.10",
            "ImageID": "sha256:traefik_v2_10_123456789abcdef",
            "State": "running",
            "Status": "Up 3 hours",
            "Created": (base_time - timedelta(hours=72)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=3)).isoformat() + "Z",
            "Network": "ingress",
            "IPAddress": "10.0.1.10",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 80,
                    "PublicPort": 80,
                    "Type": "tcp"
                },
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 443,
                    "PublicPort": 443,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "80->80/tcp, 443->443/tcp",
            "Mounts": "/var/lib/docker/volumes/traefik_config:/etc/traefik",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "swarm-cluster",
            "EndpointId": 2,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "any",
            },
        },
        "2_message-queue": {
            "Id": "swarm789def012",
            "Name": "message-queue",
            "Names": ["/message-queue"],
            "Image": "rabbitmq:3-management",
            "ImageID": "sha256:rabbitmq_3_mgmt_abcdef123456789",
            "State": "running",
            "Status": "Up 6 hours",
            "Created": (base_time - timedelta(hours=48)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=6)).isoformat() + "Z",
            "Network": "backend",
            "IPAddress": "10.0.2.20",
            "Ports": [
                {
                    "PrivatePort": 5672,
                    "Type": "tcp"
                },
                {
                    "PrivatePort": 15672,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "5672/tcp, 15672/tcp",
            "Mounts": "/var/lib/docker/volumes/rabbitmq_data:/var/lib/rabbitmq",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "swarm-cluster",
            "EndpointId": 2,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "any",
            },
        },
    }


def get_container_entity_data_kubernetes() -> Dict[str, Dict[str, Any]]:
    """Get container entity data for Kubernetes pods."""
    base_time = datetime.now()
    return {
        "3_k8s-app-1": {
            "Id": "k8s_pod_123456_abcdef",
            "Name": "k8s-app-1",
            "Names": ["/k8s-app-1"],
            "Image": "my-k8s-app:v1.2.3",
            "ImageID": "sha256:k8s_app_v1_2_3_789abcdef123456",
            "State": "running",
            "Status": "Running",
            "Created": (base_time - timedelta(hours=24)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=1)).isoformat() + "Z",
            "Network": "calico",
            "IPAddress": "10.244.1.10",
            "Ports": [
                {
                    "PrivatePort": 8080,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "8080/tcp",
            "Mounts": "/var/lib/kubelet/pods:/var/lib/kubelet/pods:ro",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "kubernetes-cluster",
            "EndpointId": 3,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "always",
            },
        },
        "3_k8s-app-2": {
            "Id": "k8s_pod_789012_ghijkl",
            "Name": "k8s-app-2",
            "Names": ["/k8s-app-2"],
            "Image": "another-k8s-app:v2.1.0",
            "ImageID": "sha256:another_k8s_app_v2_1_456789abcdef12",
            "State": "running",
            "Status": "Running",
            "Created": (base_time - timedelta(hours=12)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=2)).isoformat() + "Z",
            "Network": "calico",
            "IPAddress": "10.244.1.11",
            "Ports": [
                {
                    "PrivatePort": 3000,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "3000/tcp",
            "Mounts": "/tmp:/tmp",
            "Compose_Stack": "",
            "Compose_Service": "",
            "Compose_Version": "",
            "Environment": "kubernetes-cluster",
            "EndpointId": 3,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "always",
            },
        },
    }


def get_container_entity_data_empty() -> Dict[str, Dict[str, Any]]:
    """Get empty container entity data."""
    return {}


def get_container_entity_data_single() -> Dict[str, Dict[str, Any]]:
    """Get single container entity data."""
    base_time = datetime.now()
    return {
        "1_web-server": {
            "Id": "abc123def456",
            "Name": "web-server",
            "Names": ["/web-server"],
            "Image": "nginx:latest",
            "ImageID": "sha256:nginx_latest_1234567890abcdef",
            "State": "running",
            "Status": "Up 2 hours",
            "Created": (base_time - timedelta(hours=24)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=2)).isoformat() + "Z",
            "Network": "bridge",
            "IPAddress": "172.18.0.10",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 80,
                    "PublicPort": 8080,
                    "Type": "tcp"
                }
            ],
            "PublishedPorts": "8080->80/tcp",
            "Mounts": "none",
            "Compose_Stack": "web-stack",
            "Compose_Service": "web",
            "Compose_Version": "3.8",
            "Environment": "local",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "Privileged": False,
            "_Custom": {
                "Health_Status": "healthy",
                "Restart_Policy": "unless-stopped",
            },
        }
    }


# ---------------------------
#   Stack Entity Data Fixtures
# ---------------------------
def get_stack_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get processed stack entity data."""
    base_time = datetime.now()
    return {
        "1": {
            "Id": 1,
            "Name": "web-stack",
            "Type": 1,  # Compose
            "Status": 1,  # Active
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        "2": {
            "Id": 2,
            "Name": "monitoring-stack",
            "Type": 1,  # Compose
            "Status": 1,  # Active
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        "3": {
            "Id": 3,
            "Name": "problematic-stack",
            "Type": 1,  # Compose
            "Status": 2,  # Inactive
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        "4": {
            "Id": 4,
            "Name": "swarm-services",
            "Type": 2,  # Swarm
            "Status": 1,  # Active
            "EndpointId": 2,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        "5": {
            "Id": 5,
            "Name": "kubernetes-apps",
            "Type": 3,  # Kubernetes
            "Status": 1,  # Active
            "EndpointId": 3,
            "ConfigEntryId": "test_portainer_entry_123",
        },
    }


def get_stack_entity_data_empty() -> Dict[str, Dict[str, Any]]:
    """Get empty stack entity data."""
    return {}


def get_stack_entity_data_single() -> Dict[str, Dict[str, Any]]:
    """Get single stack entity data."""
    return {
        "1": {
            "Id": 1,
            "Name": "web-stack",
            "Type": 1,  # Compose
            "Status": 1,  # Active
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        }
    }


# ---------------------------
#   Combined Entity Data Fixtures
# ---------------------------
def get_all_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get all entity data combined."""
    return {
        "endpoints": get_endpoint_entity_data(),
        "containers": get_container_entity_data(),
        "stacks": get_stack_entity_data(),
    }


def get_mixed_environment_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get entity data for mixed environment (Docker + Swarm + K8s)."""
    containers = {}
    containers.update(get_container_entity_data())
    containers.update(get_container_entity_data_swarm())
    containers.update(get_container_entity_data_kubernetes())

    return {
        "endpoints": get_endpoint_entity_data(),
        "containers": containers,
        "stacks": get_stack_entity_data(),
    }


def get_minimal_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get minimal entity data for basic testing."""
    return {
        "endpoints": get_endpoint_entity_data_single(),
        "containers": get_container_entity_data_single(),
        "stacks": get_stack_entity_data_single(),
    }


def get_empty_entity_data() -> Dict[str, Dict[str, Any]]:
    """Get empty entity data for error testing."""
    return {
        "endpoints": {},
        "containers": {},
        "stacks": {},
    }


# ---------------------------
#   Entity State Variations
# ---------------------------
def get_container_states_all() -> Dict[str, Dict[str, Any]]:
    """Get containers with all possible states."""
    base_time = datetime.now()
    return {
        "1_running": {
            "Id": "container_running",
            "Name": "running-container",
            "State": "running",
            "Status": "Up 1 hour",
            "Created": (base_time - timedelta(hours=2)).timestamp(),
            "StartedAt": (base_time - timedelta(hours=1)).isoformat() + "Z",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "_Custom": {"Health_Status": "healthy"},
        },
        "1_stopped": {
            "Id": "container_stopped",
            "Name": "stopped-container",
            "State": "exited",
            "Status": "Exited (0) 30 minutes ago",
            "Created": (base_time - timedelta(hours=4)).timestamp(),
            "StartedAt": None,
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "_Custom": {"Health_Status": "unknown"},
        },
        "1_starting": {
            "Id": "container_starting",
            "Name": "starting-container",
            "State": "created",
            "Status": "Created",
            "Created": (base_time - timedelta(minutes=5)).timestamp(),
            "StartedAt": None,
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": None,
            "_Custom": {"Health_Status": "unknown"},
        },
        "1_unhealthy": {
            "Id": "container_unhealthy",
            "Name": "unhealthy-container",
            "State": "running",
            "Status": "Up 10 minutes (unhealthy)",
            "Created": (base_time - timedelta(hours=1)).timestamp(),
            "StartedAt": (base_time - timedelta(minutes=10)).isoformat() + "Z",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 0,
            "_Custom": {"Health_Status": "unhealthy"},
        },
        "1_restarting": {
            "Id": "container_restarting",
            "Name": "restarting-container",
            "State": "restarting",
            "Status": "Restarting (5 seconds ago)",
            "Created": (base_time - timedelta(hours=6)).timestamp(),
            "StartedAt": (base_time - timedelta(minutes=30)).isoformat() + "Z",
            "EndpointId": 1,
            "ConfigEntryId": "test_portainer_entry_123",
            "ExitCode": 1,
            "_Custom": {"Health_Status": "unknown"},
        },
    }


def get_endpoint_status_variations() -> Dict[str, Dict[str, Any]]:
    """Get endpoints with different status variations."""
    return {
        1: {
            "Id": 1,
            "Name": "healthy-endpoint",
            "Status": 1,  # Up
            "DockerVersion": "24.0.6",
            "RunningContainerCount": 5,
            "StoppedContainerCount": 1,
            "HealthyContainerCount": 4,
            "UnhealthyContainerCount": 1,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        2: {
            "Id": 2,
            "Name": "unhealthy-endpoint",
            "Status": 1,  # Up but with issues
            "DockerVersion": "23.0.3",
            "RunningContainerCount": 3,
            "StoppedContainerCount": 5,
            "HealthyContainerCount": 1,
            "UnhealthyContainerCount": 7,
            "ConfigEntryId": "test_portainer_entry_123",
        },
        3: {
            "Id": 3,
            "Name": "offline-endpoint",
            "Status": 2,  # Down
            "DockerVersion": "Unknown",
            "RunningContainerCount": 0,
            "StoppedContainerCount": 0,
            "HealthyContainerCount": 0,
            "UnhealthyContainerCount": 0,
            "ConfigEntryId": "test_portainer_entry_123",
        },
    }


# ---------------------------
#   Entity Data with Errors
# ---------------------------
def get_entity_data_with_missing_fields() -> Dict[str, Dict[str, Any]]:
    """Get entity data with missing required fields."""
    return {
        "endpoints": {
            1: {
                "Id": 1,
                "Name": "incomplete-endpoint",
                # Missing Status, DockerVersion, etc.
            }
        },
        "containers": {
            "1_incomplete": {
                "Id": "incomplete_container",
                "Name": "incomplete-container",
                # Missing State, Image, etc.
            }
        },
        "stacks": {
            "1": {
                "Id": 1,
                "Name": "incomplete-stack",
                # Missing Status, EndpointId, etc.
            }
        },
    }


def get_entity_data_with_invalid_values() -> Dict[str, Dict[str, Any]]:
    """Get entity data with invalid values."""
    return {
        "endpoints": {
            1: {
                "Id": "invalid_id",  # Should be int
                "Name": "invalid-endpoint",
                "Status": "invalid_status",  # Should be int
                "DockerVersion": None,  # Should be string
            }
        },
        "containers": {
            "1_invalid": {
                "Id": None,  # Should be string
                "Name": "invalid-container",
                "State": "invalid_state",  # Should be valid state
                "Created": "invalid_timestamp",  # Should be number
            }
        },
        "stacks": {
            "1": {
                "Id": "invalid_id",  # Should be int
                "Name": "invalid-stack",
                "Status": "invalid_status",  # Should be int
            }
        },
    }
