# Portainer Integration Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Portainer integration for Home Assistant.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Debug Logging](#debug-logging)
- [Advanced Troubleshooting](#advanced-troubleshooting)

## Quick Diagnostics

### 1. Check Integration Status
```bash
# In Home Assistant, go to:
Settings > Integrations > Portainer
```

Verify the integration shows as "Loaded" and not "Failed to load".

### 2. Check Device Availability
```bash
# In Home Assistant, go to:
Settings > Devices & Services > Devices
```

Look for your Portainer devices and check their "Last seen" timestamp.

### 3. Review Logs
```bash
# Check Home Assistant logs for Portainer errors:
Settings > System > Logs > Filter: "portainer"
```

## Common Issues

### Containers Not Appearing

**Symptoms:**
- No container devices visible in Home Assistant
- Containers missing from device list

**Possible Causes & Solutions:**

1. **Container Not Selected During Setup**
   ```bash
   # Solution: Reconfigure the integration
   Settings > Integrations > Portainer > Configure
   # Select the missing containers
   ```

2. **Portainer Endpoint Down**
   ```bash
   # Check endpoint status in Portainer UI
   # Verify endpoint shows as "Up" (Status = 1)
   ```

3. **Container Selection Filter**
   ```bash
   # The integration only shows containers you explicitly selected
   # during setup or reconfiguration
   ```

### Health Status Showing "Unknown"

**Symptoms:**
- Health sensors display "unknown" instead of health status
- Containers show as running but health is not detected

**Possible Causes & Solutions:**

1. **No Docker Health Check Configured**
   ```bash
   # The container must have a HEALTHCHECK directive in its Dockerfile
   # or be created with health check parameters

   # Example Dockerfile HEALTHCHECK:
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8080/health || exit 1
   ```

2. **Container Not Running**
   ```bash
   # Health checks only apply to running containers
   # Stopped/exited containers show "unavailable" health status
   ```

3. **Portainer API Issues**
   ```bash
   # Restart the integration to refresh API connection
   Settings > Integrations > Portainer > Reload
   ```

### Repair Issues Appearing

**Symptoms:**
- Repair issues shown for containers/endpoints
- Notifications about missing devices

**Understanding Repair Issues:**

The integration uses intelligent repair issue management:

- **3-Strike Rule**: Issues only created after 3 consecutive failures
- **Automatic Recovery**: Issues auto-resolved when devices return
- **Startup Protection**: Temporary startup issues don't trigger repairs

**Troubleshooting:**

1. **Check Portainer Connectivity**
   ```bash
   # Verify Portainer server is accessible
   curl -k https://your-portainer:9443/api/endpoints
   ```

2. **Verify Container Exists**
   ```bash
   # Check if container exists in Portainer
   # Compare with containers selected in integration
   ```

3. **Wait for Recovery**
   ```bash
   # Most repair issues resolve automatically
   # Wait 2-3 update cycles (1-2 minutes) for recovery
   ```

### Action Buttons Not Working

**Symptoms:**
- Container/stack action buttons unresponsive
- Services return errors

**Possible Causes & Solutions:**

1. **Permission Issues**
   ```bash
   # Verify your Portainer access token has sufficient permissions
   # Try with an admin-level access token
   ```

2. **Container State**
   ```bash
   # Some actions only work on running containers
   # Check container state before attempting actions
   ```

3. **Network Connectivity**
   ```bash
   # Verify Home Assistant can reach Portainer API
   # Check firewall rules and network configuration
   ```

## Debug Logging

### Enable Debug Mode

Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.portainer: debug
    custom_components.portainer.api: debug
    custom_components.portainer.coordinator: debug
```

### Useful Debug Information

**In Home Assistant logs, look for:**
- `Portainer connection error` - API connectivity issues
- `Failed to fetch endpoints` - Portainer server problems
- `Container inspection returned no data` - Individual container issues
- `Repair issue created for` - Device availability problems

### Log Analysis Tips

1. **Filter by Integration:**
   ```bash
   # In HA logs, filter for:
   "portainer" - All Portainer-related messages
   ```

2. **Check Timing:**
   ```bash
   # Look for patterns around update intervals (every 30 seconds)
   # Issues appearing at specific times may indicate periodic problems
   ```

3. **Correlate with Container Events:**
   ```bash
   # Compare Portainer logs with Docker/container events
   # Time synchronization issues can cause false failures
   ```

## Advanced Troubleshooting

### API Connectivity Testing

**Test Portainer API directly:**
```bash
# Test endpoint access
curl -k -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-portainer:9443/api/endpoints

# Test container access (replace ENDPOINT_ID and CONTAINER_ID)
curl -k -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-portainer:9443/api/endpoints/ENDPOINT_ID/docker/containers/CONTAINER_ID/json
```

### Configuration Validation

**Verify your integration configuration:**
```bash
# Check integration options
Settings > Integrations > Portainer > Configure

# Verify:
# - Host is reachable
# - Access token is valid
# - SSL settings match your Portainer setup
# - Selected endpoints/containers exist
```

### Performance Issues

**If updates are slow or timing out:**

1. **Reduce Selection Scope:**
   ```bash
   # In integration configuration, select fewer endpoints/containers
   # Large numbers of containers can slow down updates
   ```

2. **Check Network Latency:**
   ```bash
   # High latency to Portainer server can cause timeouts
   # Consider running Home Assistant closer to Portainer
   ```

3. **Monitor Resource Usage:**
   ```bash
   # Check Home Assistant system resources during updates
   # Large numbers of containers require more memory/CPU
   ```

## Getting Help

### Before Reporting Issues

1. **Enable debug logging** (see above)
2. **Wait through 3 update cycles** (90 seconds) for recovery
3. **Check Portainer server logs** for API errors
4. **Verify container/endpoints exist** in Portainer UI

### Reporting Bugs

When reporting issues, please include:

- **Home Assistant version**
- **Portainer integration version**
- **Portainer server version**
- **Debug logs** (with sensitive data redacted)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**

### Community Support

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/cbrosius/homeassistant-portainer/issues)
- **Discussions**: [Community discussions and Q&A](https://github.com/cbrosius/homeassistant-portainer/discussions)
- **HACS**: Check for integration updates in HACS

## Best Practices

### Regular Maintenance

1. **Keep Portainer Updated**: Use latest stable Portainer version
2. **Monitor Integration Health**: Check device "Last seen" timestamps regularly
3. **Review Repair Issues**: Address persistent repair issues promptly
4. **Update Access Tokens**: Rotate tokens periodically for security

### Performance Optimization

1. **Selective Monitoring**: Only select containers/endpoints you actively monitor
2. **Reasonable Update Intervals**: 30-second intervals are usually sufficient
3. **Network Optimization**: Ensure good connectivity between HA and Portainer

### Security Considerations

1. **Access Token Security**: Use dedicated tokens with minimal required permissions
2. **SSL Verification**: Enable SSL verification for production environments
3. **Network Security**: Restrict Portainer API access to Home Assistant's IP only