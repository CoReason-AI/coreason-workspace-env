import os
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def bundle_agents(source_dir: str, output_file: str, key_b64: str):
    source_path = Path(source_dir)
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for AES-256")
        
    aesgcm = AESGCM(key)
    
    bundle = {}
    for root, _, files in os.walk(source_path):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(source_path).as_posix()
                with open(file_path, 'r', encoding='utf-8') as f:
                    bundle[relative_path] = f.read()
                    
    payload = json.dumps(bundle).encode('utf-8')
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    
    # Store nonce + ciphertext together
    final_data = nonce + ciphertext
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'wb') as f:
        f.write(final_data)
        
    print(f"Successfully bundled {len(bundle)} agents into {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bundle and encrypt MCP agents.")
    parser.add_argument("--source", default="src/agents", help="Source directory of agents")
    parser.add_argument("--output", default="dist/coreason_mcp_bundle.enc", help="Output file path")
    
    args = parser.parse_args()
    key_b64 = os.environ.get("MCP_BUNDLE_KEY")
    
    if not key_b64:
        # Generate a random key for testing if not provided, just to let the build pass in local dev
        # In production CI, this should be securely injected.
        test_key = AESGCM.generate_key(bit_length=256)
        key_b64 = base64.b64encode(test_key).decode('utf-8')
        print(f"WARNING: MCP_BUNDLE_KEY not set. Generated a random test key: {key_b64}")
        
    bundle_agents(args.source, args.output, key_b64)
