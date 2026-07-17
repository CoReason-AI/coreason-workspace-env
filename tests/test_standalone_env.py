import os
import sys
import psycopg2

import urllib.request
from urllib.error import URLError, HTTPError

def check_postgres():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB', 'coreason'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            host=os.getenv('POSTGRES_HOST', 'postgres_checkpointer'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        conn.close()
        return "SUCCESS: Connected to Postgres"
    except Exception as e:
        return f"FAILED: Postgres - {e}"



def check_url(url, name, expect_403=False):
    if not url:
        return f"FAILED: {name} - URL is empty"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return f"SUCCESS: {name} endpoint reachable ({response.getcode()})"
    except HTTPError as e:
        if expect_403 and e.code == 403:
            return f"SUCCESS: {name} endpoint reachable but returned HTTP 403 (Expected)"
        return f"SUCCESS: {name} endpoint reachable but returned HTTP {e.code}"
    except URLError as e:
        return f"FAILED: {name} - {e.reason}"
    except Exception as e:
        return f"FAILED: {name} - {e}"

if __name__ == "__main__":
    print("====================")
    print("Testing Postgres...")
    print(check_postgres())
    

    
    print("\nTesting Vault...")
    vault_addr = os.getenv('VAULT_ADDR', 'http://vault:8200')
    print(check_url(f"{vault_addr}/v1/sys/health", "Vault"))
    
    print("\nTesting S3 Endpoint...")
    s3_url = os.getenv('WORM_S3_ENDPOINT', 'http://minio:9000')
    print(check_url(s3_url, "S3", expect_403=True))
    
    print("\nTesting LLM Base URL...")
    llm_url = os.getenv('LLM_BASE_URL', 'http://ollama:11434/v1')
    print(check_url(f"{llm_url}/models", "LLM API"))
    print("====================")
