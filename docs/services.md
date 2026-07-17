# Bare-Metal Services: Standalone Single-Node Deployments

While large-scale enterprise deployments utilize Kubernetes or Managed Cloud Services (see the [Deployment Guide](deployment_guide.md)), you may need to deploy the CoReason platform onto a single standalone virtual machine or bare-metal computer. 

To ensure **cross-platform parity** and strict deterministic dependencies, the standalone deployment still utilizes the `docker-compose.standalone.yaml` stack. However, for a production-like environment, this stack must be managed by the native OS service manager. This ensures the platform starts silently on boot, auto-restarts on failure, and writes standard logs.

Below are the parity instructions for configuring this on Linux and Windows.

---

## Linux: Systemd Integration

On modern Linux distributions (Ubuntu, RHEL, Debian), `systemd` is the standard service manager. We will create a `systemd` unit that manages the lifecycle of the Docker Compose stack.

### 1. Create the Systemd Unit File

Create a new file at `/etc/systemd/system/coreason.service`:

```ini
[Unit]
Description=CoReason Workspace Environment (Standalone Docker Compose)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/coreason-workspace-env

# Startup
ExecStart=/usr/bin/docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d --build

# Shutdown
ExecStop=/usr/bin/docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml down

[Install]
WantedBy=multi-user.target
```

> [!NOTE]
> Make sure to update the `WorkingDirectory` path to wherever you cloned the repository.

### 2. Enable and Start the Service

Reload the daemon and enable the service to start automatically on system boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable coreason
sudo systemctl start coreason
```

To view the service status and logs:
```bash
sudo systemctl status coreason
```

---

## Windows: NSSM Integration

Windows does not use `systemd`. To achieve exact service parity on a standalone Windows Server or Windows Desktop machine, we utilize [NSSM (Non-Sucking Service Manager)](http://nssm.cc/) to wrap the Docker Compose commands into a native Windows Background Service.

### 1. Prerequisites
1. Ensure **Docker Desktop** (or Docker Engine for Windows Server) is installed and configured to start automatically with Windows.
2. Download `nssm.exe` and place it in a system path (or inside your project directory).

### 2. Create the Startup Script

Create a `start_coreason.bat` file in the root of your project:

```bat
@echo off
cd /d "%~dp0"
docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d --build
```

### 3. Install the Windows Service

Open an **Administrator PowerShell** prompt and use NSSM to install the script as a service:

```powershell
nssm install CoReasonService "C:\path\to\coreason-workspace-env\start_coreason.bat"
```

### 4. Configure Service Properties

Set the service to run automatically on boot, and route standard output/error to a log file for observability parity with `systemd`:

```powershell
nssm set CoReasonService AppDirectory "C:\path\to\coreason-workspace-env"
nssm set CoReasonService Description "CoReason Workspace Environment"
nssm set CoReasonService AppStdout "C:\path\to\coreason-workspace-env\service.log"
nssm set CoReasonService AppStderr "C:\path\to\coreason-workspace-env\service-error.log"
```

### 5. Start the Service

Finally, start the native Windows service:

```powershell
Start-Service CoReasonService
```

You can now manage the platform identically to any other Windows service via the `services.msc` GUI or PowerShell.
