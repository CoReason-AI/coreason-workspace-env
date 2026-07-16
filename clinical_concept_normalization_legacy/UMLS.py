import os
import sys
import json
import asyncio
import datetime
import httpx

API_KEY = os.environ.get("UMLS_API_KEY", "c0581274-ac93-425b-9f17-cb70f9bca206")
BASE_URL = "https://uts-ws.nlm.nih.gov/rest"

async def fetch_json(client, url, params=None):
    """Fetches JSON content from NLM UTS API with a retry mechanism."""
    for attempt in range(3):
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Concept or page not found, return empty dictionary/list representation
                return None
        except httpx.RequestError as e:
            if attempt == 2:
                sys.stderr.write(f"Warning: Failed to fetch {url} after 3 attempts: {e}\n")
            await asyncio.sleep(1.0 * (attempt + 1))
    return None

async def check_subsumption(client, start_cui, target_cui, max_depth=3):
    """
    Performs a Breadth-First Search (BFS) to traverse the parent concept hierarchy 
    and checks if start_cui is subsumed by (a descendant of) target_cui.
    """
    if not start_cui or not target_cui or start_cui == target_cui:
        return start_cui == target_cui
        
    visited = {start_cui}
    queue = [(start_cui, 0)]
    
    while queue:
        current_cui, depth = queue.pop(0)
        if depth >= max_depth:
            continue
            
        relations_url = f"{BASE_URL}/content/current/CUI/{current_cui}/relations"
        params = {"apiKey": API_KEY, "sabs": "MTH"}
        relations_res = await fetch_json(client, relations_url, params)
        
        if relations_res and "result" in relations_res:
            relations_list = relations_res["result"]
            if isinstance(relations_list, list):
                for rel in relations_list:
                    rel_id_url = rel.get("relatedId")
                    label = rel.get("relationLabel")
                    
                    # Extract target CUI from the relation URL
                    rel_cui = None
                    if rel_id_url and "CUI/" in rel_id_url:
                        rel_cui = rel_id_url.rstrip("/").split("CUI/")[-1]
                        
                    if rel_cui and rel_cui.startswith("C"):
                        # Target is parent if relation label is PAR (Parent) or RN (Related Narrower -> source is narrower)
                        if label in ("PAR", "RN"):
                            if rel_cui == target_cui:
                                return True
                            if rel_cui not in visited:
                                visited.add(rel_cui)
                                queue.append((rel_cui, depth + 1))
    return False

async def get_ontology_profile(umls_cui, subsumption_target_cui=None):
    """Fetches concept metadata, atoms/synonyms, crosswalk codes, relations and definitions to construct the dossier."""
    async with httpx.AsyncClient() as client:
        # Define URLs
        info_url = f"{BASE_URL}/content/current/CUI/{umls_cui}"
        atoms_url = f"{BASE_URL}/content/current/CUI/{umls_cui}/atoms"
        relations_url = f"{BASE_URL}/content/current/CUI/{umls_cui}/relations"
        definitions_url = f"{BASE_URL}/content/current/CUI/{umls_cui}/definitions"
        
        # Define task parameters
        params = {"apiKey": API_KEY}
        atoms_params = {"apiKey": API_KEY, "sabs": "SNOMEDCT_US,MDR,ICD10CM,MSH"}
        relations_params = {"apiKey": API_KEY, "sabs": "MTH"}
        
        # Fetch data concurrently
        tasks = [
            fetch_json(client, info_url, params),
            fetch_json(client, atoms_url, atoms_params),
            fetch_json(client, relations_url, relations_params),
            fetch_json(client, definitions_url, params),
        ]
        
        results = await asyncio.gather(*tasks)
        info_res, atoms_res, relations_res, defs_res = results
        
        # 1. Extract Semantic Type
        semantic_type = "None"
        if info_res and "result" in info_res:
            sem_types = info_res["result"].get("semanticTypes", [])
            if sem_types:
                semantic_type = ", ".join([st.get("name", "") for st in sem_types if st.get("name")])
        
        # 2. Extract Synonyms and Crosswalk Codes
        synonyms = []
        snomed_ct_codes = set()
        meddra_llt_codes = set()
        meddra_pt_codes = set()
        meddra_soc_codes = set()
        icd_10_codes = set()
        mesh_terms = set()
        
        if atoms_res and "result" in atoms_res:
            atoms_list = atoms_res["result"]
            if isinstance(atoms_list, list):
                for atom in atoms_list:
                    name = atom.get("name")
                    if name and name not in synonyms:
                        synonyms.append(name)
                        
                    source = atom.get("rootSource")
                    code_raw = atom.get("code")
                    
                    # Extract clean code value if it is presented as a URL path component
                    code_val = None
                    if code_raw:
                        if code_raw.startswith("http"):
                            code_val = code_raw.rstrip("/").split("/")[-1]
                        else:
                            code_val = code_raw
                            
                    if source == "SNOMEDCT_US" and code_val:
                        snomed_ct_codes.add(code_val)
                    elif source == "MDR" and code_val:
                        tty = atom.get("termType")
                        if tty == "LLT":
                            meddra_llt_codes.add(code_val)
                        elif tty == "PT":
                            meddra_pt_codes.add(code_val)
                        elif tty == "SOC":
                            meddra_soc_codes.add(code_val)
                    elif source == "ICD10CM" and code_val:
                        icd_10_codes.add(code_val)
                    elif source == "MSH":
                        if name:
                            mesh_terms.add(name)
                        elif code_val:
                            mesh_terms.add(code_val)
                            
        # 3. Extract Hierarchy Parents and Children
        parent_concepts = set()
        child_concepts = set()
        if relations_res and "result" in relations_res:
            relations_list = relations_res["result"]
            if isinstance(relations_list, list):
                for rel in relations_list:
                    rel_id_url = rel.get("relatedId")
                    label = rel.get("relationLabel")
                    
                    rel_cui = None
                    if rel_id_url and "CUI/" in rel_id_url:
                        rel_cui = rel_id_url.rstrip("/").split("CUI/")[-1]
                        
                    if rel_cui and rel_cui.startswith("C"):
                        # Target is parent if relation label is PAR or RN
                        if label in ("PAR", "RN"):
                            parent_concepts.add(rel_cui)
                        # Target is child if relation label is CHD or RB
                        elif label in ("CHD", "RB"):
                            child_concepts.add(rel_cui)
                            
        # 4. Extract Definitions
        msh_raw = ""
        nci_raw = ""
        hpo_raw = ""
        if defs_res and "result" in defs_res:
            defs_list = defs_res["result"]
            if isinstance(defs_list, list):
                for df in defs_list:
                    src = df.get("rootSource")
                    val = df.get("value")
                    if val:
                        if src == "MSH":
                            msh_raw = val
                        elif src == "NCI":
                            nci_raw = val
                        elif src == "HPO":
                            hpo_raw = val
                            
        # 5. Execute Subsumption Check (if target CUI provided)
        is_subsumed = False
        if subsumption_target_cui and subsumption_target_cui != "None":
            is_subsumed = await check_subsumption(client, umls_cui, subsumption_target_cui)
            
        # 6. Build Provenance receipts
        uris = [info_url, atoms_url, relations_url, definitions_url]
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        
        output_payload = {
            "umls_cui": umls_cui,
            "semantic_type": semantic_type,
            "synonyms": synonyms,
            "crosswalks": {
                "snomed_ct_codes": sorted(list(snomed_ct_codes)),
                "meddra_llt_codes": sorted(list(meddra_llt_codes)),
                "meddra_pt_codes": sorted(list(meddra_pt_codes)),
                "meddra_soc_codes": sorted(list(meddra_soc_codes)),
                "icd_10_codes": sorted(list(icd_10_codes)),
                "mesh_terms": sorted(list(mesh_terms))
            },
            "hierarchy": {
                "parent_concepts": sorted(list(parent_concepts)),
                "child_concepts": sorted(list(child_concepts))
            },
            "subsumption_check": {
                "target_cui_tested": subsumption_target_cui if subsumption_target_cui else "None",
                "is_subsumed": is_subsumed
            },
            "definitions": {
                "msh_raw": msh_raw,
                "nci_raw": nci_raw,
                "hpo_raw": hpo_raw
            },
            "provenance_receipts": {
                "umls_query_timestamp": timestamp,
                "authoritative_source_uris": uris
            }
        }
        return output_payload

async def main():
    # Read input payload from command line arguments or standard input
    input_text = None
    if len(sys.argv) > 1:
        input_text = sys.argv[1].strip()
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
        
    if not input_text:
        sys.stderr.write("Error: No input payload provided.\n")
        sys.exit(1)
        
    input_payload = None

    # 1. Try directly parsing the full input as JSON
    try:
        input_payload = json.loads(input_text)
    except Exception:
        pass

    # 2. Try parsing by finding markdown block ```json ... ```
    if not input_payload and "```" in input_text:
        try:
            parts = input_text.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0].strip()
                input_payload = json.loads(json_part)
            else:
                parts = input_text.split("```")
                if len(parts) > 1:
                    json_part = parts[1].split("```")[0].strip()
                    input_payload = json.loads(json_part)
        except Exception:
            pass

    # 3. Try finding first '{' and last '}'
    if not input_payload:
        try:
            start_idx = input_text.find('{')
            end_idx = input_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_candidate = input_text[start_idx : end_idx + 1]
                input_payload = json.loads(json_candidate)
        except Exception:
            pass

    # 4. Extract all unique CUIs and subsumption targets to process
    cuis_to_process = []  # list of tuples: (cui, target_cui)

    if isinstance(input_payload, dict):
        if "tagged_chunks" in input_payload:
            chunks = input_payload["tagged_chunks"]
            if isinstance(chunks, list):
                for chunk in chunks:
                    if isinstance(chunk, dict):
                        c = chunk.get("umls_cui")
                        target = chunk.get("subsumption_target_cui")
                        if c and c not in [item[0] for item in cuis_to_process]:
                            cuis_to_process.append((c, target))
                            
        # Also check direct root level fields
        root_c = input_payload.get("umls_cui")
        root_target = input_payload.get("subsumption_target_cui")
        if root_c and root_c not in [item[0] for item in cuis_to_process]:
            cuis_to_process.append((root_c, root_target))

    elif isinstance(input_payload, list):
        for el in input_payload:
            if isinstance(el, dict):
                c = el.get("umls_cui")
                target = el.get("subsumption_target_cui")
                if c and c not in [item[0] for item in cuis_to_process]:
                    cuis_to_process.append((c, target))
            elif isinstance(el, str):
                cleaned = el.strip().strip("'\"")
                if cleaned.startswith("C") and len(cleaned) >= 7 and cleaned[1:].isdigit():
                    if cleaned not in [item[0] for item in cuis_to_process]:
                        cuis_to_process.append((cleaned, None))
    else:
        # Fallback to direct raw CUI string
        cleaned_raw = input_text.strip().strip("'\"")
        if cleaned_raw.startswith("C") and len(cleaned_raw) >= 7 and cleaned_raw[1:].isdigit():
            cuis_to_process.append((cleaned_raw, None))

    if not cuis_to_process:
        sys.stderr.write("Error: Missing required field 'umls_cui'.\n")
        sys.exit(1)

    # 5. Process all concepts concurrently
    try:
        tasks = [get_ontology_profile(c, target) for c, target in cuis_to_process]
        profiles = await asyncio.gather(*tasks)
        
        # Build backward-compatible response
        if len(profiles) == 1:
            output_payload = profiles[0]
            # Avoid circular reference by copying the list element
            output_payload["umls_profiles"] = [profiles[0].copy()]
        else:
            output_payload = {
                "umls_profiles": profiles
            }
            
        print(json.dumps(output_payload, indent=2))
    except Exception as e:
        sys.stderr.write(f"Error executing profile retrieval: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
