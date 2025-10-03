"""API response fixtures for Portainer integration testing."""

from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
import random


# ---------------------------
#   Endpoints API Responses
# ---------------------------
def get_endpoints_response() -> List[Dict[str, Any]]:
    """Get mock endpoints response."""
    return [
        {
            "Id": 1,
            "Name": "local",
            "Type": 1,  # Docker
            "Status": 1,  # Up
            "Snapshots": [
                {
                    "DockerVersion": "24.0.6",
                    "Swarm": False,
                    "TotalCPU": 8,
                    "TotalMemory": 16777216000,  # 16GB in bytes
                    "RunningContainerCount": 5,
                    "StoppedContainerCount": 2,
                    "HealthyContainerCount": 4,
                    "UnhealthyContainerCount": 1,
                    "VolumeCount": 12,
                    "ImageCount": 25,
                    "ServiceCount": 0,
                    "StackCount": 3,
                }
            ],
        },
        {
            "Id": 2,
            "Name": "swarm-cluster",
            "Type": 2,  # Docker Swarm
            "Status": 1,  # Up
            "Snapshots": [
                {
                    "DockerVersion": "23.0.3",
                    "Swarm": True,
                    "TotalCPU": 16,
                    "TotalMemory": 33554432000,  # 32GB in bytes
                    "RunningContainerCount": 8,
                    "StoppedContainerCount": 1,
                    "HealthyContainerCount": 7,
                    "UnhealthyContainerCount": 1,
                    "VolumeCount": 20,
                    "ImageCount": 45,
                    "ServiceCount": 5,
                    "StackCount": 6,
                }
            ],
        },
        {
            "Id": 3,
            "Name": "kubernetes-cluster",
            "Type": 3,  # Kubernetes
            "Status": 1,  # Up
            "Snapshots": [
                {
                    "DockerVersion": "25.0.0",
                    "Swarm": False,
                    "TotalCPU": 32,
                    "TotalMemory": 67108864000,  # 64GB in bytes
                    "RunningContainerCount": 15,
                    "StoppedContainerCount": 3,
                    "HealthyContainerCount": 12,
                    "UnhealthyContainerCount": 3,
                    "VolumeCount": 30,
                    "ImageCount": 80,
                    "ServiceCount": 12,
                    "StackCount": 8,
                }
            ],
        },
        {
            "Id": 4,
            "Name": "offline-endpoint",
            "Type": 1,  # Docker
            "Status": 2,  # Down
            "Snapshots": [],
        },
    ]


def get_endpoints_response_empty() -> List[Dict[str, Any]]:
    """Get empty endpoints response."""
    return []


def get_endpoints_response_malformed() -> List[Dict[str, Any]]:
    """Get malformed endpoints response for error testing."""
    return [
        {
            "Id": "invalid_id",  # Should be integer
            "Name": None,  # Should be string
            "Type": "invalid_type",  # Should be integer
            "Status": "invalid_status",  # Should be integer
        }
    ]


# ---------------------------
#   Containers API Responses
# ---------------------------
def get_containers_response() -> List[Dict[str, Any]]:
    """Get mock containers response."""
    base_time = datetime.now()
    return [
        {
            "Id": "abc123def456",
            "Names": ["/web-server"],
            "Image": "nginx:latest",
            "State": "running",
            "Status": "Up 2 hours",
            "Ports": [
                {"IP": "0.0.0.0", "PrivatePort": 80, "PublicPort": 8080, "Type": "tcp"}
            ],
            "Created": int((base_time - timedelta(hours=24)).timestamp()),
            "Labels": {
                "com.docker.compose.project": "web-stack",
                "com.docker.compose.service": "web",
                "com.docker.compose.version": "3.8",
                "traefik.enable": "true",
                "traefik.http.routers.web.rule": "Host(`example.com`)",
            },
        },
        {
            "Id": "def789ghi012",
            "Names": ["/database"],
            "Image": "postgres:15",
            "State": "running",
            "Status": "Up 30 minutes",
            "Ports": [{"IP": "127.0.0.1", "PrivatePort": 5432, "Type": "tcp"}],
            "Created": int((base_time - timedelta(hours=12)).timestamp()),
            "Labels": {
                "com.docker.compose.project": "web-stack",
                "com.docker.compose.service": "db",
                "com.docker.compose.version": "3.8",
            },
        },
        {
            "Id": "ghi345jkl678",
            "Names": ["/cache"],
            "Image": "redis:7-alpine",
            "State": "running",
            "Status": "Up 1 hour",
            "Ports": [{"PrivatePort": 6379, "Type": "tcp"}],
            "Created": int((base_time - timedelta(hours=6)).timestamp()),
            "Labels": {
                "com.docker.compose.project": "web-stack",
                "com.docker.compose.service": "cache",
                "com.docker.compose.version": "3.8",
            },
        },
        {
            "Id": "jkl901mno234",
            "Names": ["/monitoring"],
            "Image": "prometheus:latest",
            "State": "running",
            "Status": "Up 45 minutes",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 9090,
                    "PublicPort": 9090,
                    "Type": "tcp",
                }
            ],
            "Created": int((base_time - timedelta(hours=8)).timestamp()),
            "Labels": {},
        },
        {
            "Id": "mno567pqr890",
            "Names": ["/backup-service"],
            "Image": "restic/restic",
            "State": "exited",
            "Status": "Exited (0) 10 minutes ago",
            "Ports": [],
            "Created": int((base_time - timedelta(hours=48)).timestamp()),
            "Labels": {
                "backup.schedule": "daily",
                "backup.source": "/data",
            },
        },
        {
            "Id": "pqr123stu456",
            "Names": ["/unhealthy-app"],
            "Image": "myapp:latest",
            "State": "running",
            "Status": "Up 5 minutes (unhealthy)",
            "Ports": [
                {
                    "IP": "0.0.0.0",
                    "PrivatePort": 3000,
                    "PublicPort": 3000,
                    "Type": "tcp",
                }
            ],
            "Created": int((base_time - timedelta(hours=2)).timestamp()),
            "Labels": {
                "com.docker.compose.project": "problematic-stack",
                "com.docker.compose.service": "app",
            },
        },
        {
            "Id": "stu789vwx012",
            "Names": ["/legacy-app"],
            "Image": "old-app:1.0",
            "State": "created",
            "Status": "Created",
            "Ports": [],
            "Created": int((base_time - timedelta(days=7)).timestamp()),
            "Labels": {},
        },
    ]


def get_containers_response_empty() -> List[Dict[str, Any]]:
    """Get empty containers response."""
    return []


def get_containers_response_malformed() -> List[Dict[str, Any]]:
    """Get malformed containers response for error testing."""
    return [
        {
            "Id": None,  # Should be string
            "Names": "invalid_names",  # Should be array
            "Image": None,  # Should be string
            "State": None,  # Should be string
        }
    ]


# ---------------------------
#   Container Inspection Responses
# ---------------------------
def get_container_inspect_response(container_id: str) -> Dict[str, Any]:
    """Get mock container inspection response."""
    base_time = datetime.now()
    container_configs = {
        "abc123def456": {
            "name": "web-server",
            "image": "nginx:latest",
            "state": "running",
            "health_status": "healthy",
        },
        "def789ghi012": {
            "name": "database",
            "image": "postgres:15",
            "state": "running",
            "health_status": "healthy",
        },
        "ghi345jkl678": {
            "name": "cache",
            "image": "redis:7-alpine",
            "state": "running",
            "health_status": "healthy",
        },
        "jkl901mno234": {
            "name": "monitoring",
            "image": "prometheus:latest",
            "state": "running",
            "health_status": "healthy",
        },
        "mno567pqr890": {
            "name": "backup-service",
            "image": "restic/restic",
            "state": "exited",
            "exit_code": 0,
        },
        "pqr123stu456": {
            "name": "unhealthy-app",
            "image": "myapp:latest",
            "state": "running",
            "health_status": "unhealthy",
        },
        "stu789vwx012": {
            "name": "legacy-app",
            "image": "old-app:1.0",
            "state": "created",
        },
    }

    config = container_configs.get(container_id, container_configs["abc123def456"])

    return {
        "Id": container_id,
        "Created": (base_time - timedelta(hours=24)).isoformat() + "Z",
        "State": {
            "Status": config["state"],
            "Running": config["state"] == "running",
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": 12345 if config["state"] == "running" else 0,
            "ExitCode": 0 if config["state"] == "running" else 1,
            "Error": "",
            "StartedAt": (
                (base_time - timedelta(hours=2)).isoformat() + "Z"
                if config["state"] == "running"
                else None
            ),
            "FinishedAt": (
                None
                if config["state"] == "running"
                else (base_time - timedelta(minutes=10)).isoformat() + "Z"
            ),
            "Health": (
                {
                    "Status": config["health_status"],
                    "FailingStreak": 0 if config["health_status"] == "healthy" else 3,
                    "Log": [
                        {
                            "Start": (base_time - timedelta(minutes=5)).isoformat()
                            + "Z",
                            "End": (base_time - timedelta(minutes=4)).isoformat() + "Z",
                            "ExitCode": 0,
                            "Output": "Health check passed",
                        }
                    ],
                }
                if config["state"] == "running"
                else None
            ),
        },
        "Image": f"sha256:{'0' * 64}",
        "Name": f"/{config['name']}",
        "RestartPolicy": {
            "Name": "unless-stopped",
            "MaximumRetryCount": 3,
        },
        "HostConfig": {
            "NetworkMode": "bridge",
            "Privileged": False,
            "RestartPolicy": {
                "Name": "unless-stopped",
                "MaximumRetryCount": 3,
            },
        },
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                    "NetworkID": f"network_{container_id[:12]}",
                    "EndpointID": f"endpoint_{container_id[:12]}",
                    "Gateway": "172.18.0.1",
                    "IPAddress": f"172.18.0.{random.randint(2, 254)}",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:12:00:02",
                }
            }
        },
        "Mounts": (
            [
                {
                    "Type": "volume",
                    "Name": f"volume_{config['name']}",
                    "Source": f"/var/lib/docker/volumes/volume_{config['name']}/_data",
                    "Destination": "/data",
                    "Driver": "local",
                    "Mode": "rw",
                    "RW": True,
                    "Propagation": "",
                }
            ]
            if config["name"] in ["database", "monitoring"]
            else []
        ),
        "Config": {
            "Env": (
                [
                    "POSTGRES_PASSWORD=secret",
                    "POSTGRES_DB=mydb",
                ]
                if "postgres" in config["image"]
                else (
                    [
                        "REDIS_PASSWORD=secret",
                    ]
                    if "redis" in config["image"]
                    else []
                )
            ),
            "Labels": {
                "com.docker.compose.project": "web-stack",
                "com.docker.compose.service": config["name"],
            },
        },
    }


# ---------------------------
#   Stacks API Responses
# ---------------------------
def get_stacks_response() -> List[Dict[str, Any]]:
    """Get mock stacks response."""
    return [
        {
            "Id": 1,
            "Name": "web-stack",
            "Type": 1,  # Compose
            "EndpointId": 1,
            "Status": 1,  # Active
            "CreationDate": int((datetime.now() - timedelta(days=30)).timestamp()),
            "UpdateDate": int((datetime.now() - timedelta(hours=2)).timestamp()),
        },
        {
            "Id": 2,
            "Name": "monitoring-stack",
            "Type": 1,  # Compose
            "EndpointId": 1,
            "Status": 1,  # Active
            "CreationDate": int((datetime.now() - timedelta(days=15)).timestamp()),
            "UpdateDate": int((datetime.now() - timedelta(hours=1)).timestamp()),
        },
        {
            "Id": 3,
            "Name": "problematic-stack",
            "Type": 1,  # Compose
            "EndpointId": 1,
            "Status": 2,  # Inactive
            "CreationDate": int((datetime.now() - timedelta(days=7)).timestamp()),
            "UpdateDate": int((datetime.now() - timedelta(days=1)).timestamp()),
        },
        {
            "Id": 4,
            "Name": "swarm-services",
            "Type": 2,  # Swarm
            "EndpointId": 2,
            "Status": 1,  # Active
            "CreationDate": int((datetime.now() - timedelta(days=20)).timestamp()),
            "UpdateDate": int((datetime.now() - timedelta(hours=6)).timestamp()),
        },
        {
            "Id": 5,
            "Name": "kubernetes-apps",
            "Type": 3,  # Kubernetes
            "EndpointId": 3,
            "Status": 1,  # Active
            "CreationDate": int((datetime.now() - timedelta(days=10)).timestamp()),
            "UpdateDate": int((datetime.now() - timedelta(hours=3)).timestamp()),
        },
    ]


def get_stacks_response_empty() -> List[Dict[str, Any]]:
    """Get empty stacks response."""
    return []


# ---------------------------
#   Error Response Scenarios
# ---------------------------
def get_error_response_404() -> Dict[str, Any]:
    """Get 404 error response."""
    return {
        "message": "Not found",
        "details": "The requested resource was not found",
    }


def get_error_response_500() -> Dict[str, Any]:
    """Get 500 error response."""
    return {
        "message": "Internal server error",
        "details": "An unexpected error occurred on the server",
    }


def get_error_response_401() -> Dict[str, Any]:
    """Get 401 error response."""
    return {
        "message": "Unauthorized",
        "details": "Invalid API key or authentication failed",
    }


def get_error_response_403() -> Dict[str, Any]:
    """Get 403 error response."""
    return {
        "message": "Forbidden",
        "details": "You don't have permission to access this resource",
    }


def get_error_response_timeout() -> Dict[str, Any]:
    """Get timeout error response."""
    return {
        "message": "Request timeout",
        "details": "The request timed out while waiting for a response",
    }


def get_error_response_connection_error() -> Dict[str, Any]:
    """Get connection error response."""
    return {
        "message": "Connection error",
        "details": "Failed to establish connection to Portainer server",
    }


# ---------------------------
#   System Information Response
# ---------------------------
def get_system_info_response() -> Dict[str, Any]:
    """Get mock system information response."""
    return {
        "version": "2.19.4",
        "platform": "linux",
        "architecture": "amd64",
        "os": "Debian GNU/Linux 12 (bookworm)",
        "kernel_version": "6.1.0-13-amd64",
        "api_version": "1.43",
        "build_time": "2024-01-15T10:30:00Z",
        "git_commit": "abc123def456",
        "server": {
            "name": "portainer-server",
            "version": "2.19.4",
        },
        "security": {
            "authentication": True,
            "tls": True,
        },
    }


# ---------------------------
#   Authentication Response
# ---------------------------
def get_auth_response_success() -> Dict[str, Any]:
    """Get successful authentication response."""
    return {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token_signature",
    }


def get_auth_response_invalid_credentials() -> Dict[str, Any]:
    """Get invalid credentials response."""
    return {
        "message": "Invalid credentials",
        "details": "The provided username or password is incorrect",
    }


# ---------------------------
#   Container Actions Response
# ---------------------------
def get_container_recreate_response() -> Dict[str, Any]:
    """Get container recreate response."""
    return {
        "message": "Container recreate initiated",
        "container_id": "abc123def456",
        "operation_id": "recreate_123456",
    }


def get_container_recreate_error_response() -> Dict[str, Any]:
    """Get container recreate error response."""
    return {
        "message": "Failed to recreate container",
        "details": "Container is currently running and cannot be recreated",
        "error_code": "CONTAINER_RUNNING",
    }
