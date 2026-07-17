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

## Windows: WinSW Integration

Windows does not use `systemd`. To achieve exact service parity on a standalone Windows Server or Desktop machine, we utilize [WinSW (Windows Service Wrapper)](https://github.com/winsw/winsw) — a modern, actively maintained standard backed by the .NET Foundation. This allows us to use a declarative XML configuration that closely mirrors the behavior of `systemd`.

### 1. Prerequisites
1. Ensure **Docker Desktop** (or Docker Engine) is installed and configured to start automatically with Windows. *(Note: Windows Home Edition with WSL2 is fully supported!)*
2. Download the latest `WinSW-x64.exe` from the [official releases](https://github.com/winsw/winsw/releases) and place it in your project root directory. Rename it to `coreason-service.exe`.

### 2. Create the Service Definition (XML)

Create a file named `coreason-service.xml` in the same directory as the executable:

```xml
<service>
  <id>coreason</id>
  <name>CoReason Workspace Environment</name>
  <description>Standalone Docker Compose stack for CoReason agents.</description>
  
  <!-- Startup Command -->
  <executable>docker</executable>
  <arguments>compose -f docker-compose.yaml -f docker-compose.standalone.yaml up --build</arguments>
  
  <!-- Shutdown Command -->
  <stopexecutable>docker</stopexecutable>
  <stoparguments>compose -f docker-compose.yaml -f docker-compose.standalone.yaml down</stoparguments>
  
  <!-- Log rotation parity -->
  <log mode="roll"></log>
</service>
```

> [!NOTE]
> Unlike the CLI `up -d` command, WinSW expects the process to run in the foreground (`up` without `-d`) so it can natively capture standard output logs and automatically restart the service if it crashes!

### 3. Install and Start the Service

Open an **Administrator PowerShell** prompt, navigate to your project directory, and run:

```powershell
.\coreason-service.exe install
.\coreason-service.exe start
```

You can now manage the platform identically to any native Windows service via the `services.msc` GUI or by using PowerShell (`Stop-Service coreason`).
