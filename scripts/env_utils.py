import subprocess
import time
import requests
import urllib.request
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_docker_running() -> bool:
    """Verify that the Docker daemon is active and accessible."""
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_observability_stack() -> bool:
    """Bootstrap the local Docker containers."""
    if not check_docker_running():
        logger.error("Docker daemon is not running. Please start Docker Desktop or the Docker service.")
        return False
    
    logger.info("Starting local backend stack...")
    try:
        # Assuming docker-compose.yaml is in the project root
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        logger.info("Docker containers started successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start docker containers: {e}")
        return False

def verify_observability_connection(url: str = "http://localhost:16686", timeout: int = 30) -> bool:
    """Ping the Jaeger UI to ensure the observability layer is ready for traces."""
    logger.info(f"Waiting for Jaeger observability backend to become healthy at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info("Jaeger is healthy and ready to receive traces!")
                return True
        except requests.exceptions.RequestException:
            pass
            
        time.sleep(2)
        
    logger.error("Timed out waiting for Jaeger to become healthy.")
    return False

if __name__ == "__main__":
    start_observability_stack()
    verify_observability_connection()
