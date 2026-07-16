# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_gitops

"""
AGENT INSTRUCTION: Evaluate Designated Medical Event (DME) status using BioMCP.
Supports both single 'target_event' schema and 'umls_profiles' batch schema inputs.
"""

import os
import sys
import json
import asyncio
import re
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Standard list of Designated Medical Event (DME) keywords / conditions
# These are conditions that are inherently serious (e.g., EMA DME list)
DME_KEYWORDS = [
    r"stevens-johnson",
    r"toxic epidermal necrolysis",
    r"erythema multiforme",
    r"anaphylaxis",
    r"anaphylactic",
    r"angioedema",
    r"sepsis",
    r"septic shock",
    r"myocardial infarction",
    r"cardiac arrest",
    r"torsade de pointes",
    r"ventricular fibrillation",
    r"ventricular tachycardia",
    r"myocarditis",
    r"pericarditis",
    r"pulmonary embolism",
    r"stroke",
    r"cerebrovascular accident",
    r"acute liver failure",
    r"hepatic failure",
    r"hepatic necrosis",
    r"acute renal failure",
    r"acute kidney injury",
    r"acute pancreatitis",
    r"aplastic an?emia",
    r"agranulocytosis",
    r"thrombocytopenia",
    r"pancytopenia",
    r"h?emolytic an?emia",
    r"disseminated intravascular coagulation",
    r"interstitial lung disease",
    r"alveolitis",
    r"pulmonary hypertension",
    r"bronchospasm",
    r"seizure",
    r"convulsion",
    r"encephalopathy",
    r"guillain-barre",
    r"dementia",
    r"peripheral neuropathy",
    r"neuroleptic malignant syndrome",
    r"blindness",
    r"deafness",
    r"optic neuritis",
    r"sudden death",
    r"neutropenic sepsis",
    r"oculogyric crisis",
    r"pancreatitis haemorrhagic",
    r"toxic hepatitis",
    r"veno-occlusive liver disease",
    r"haemorrhage",
    r"rhabdomyolysis",
    r"asphyxia",
    r"tardive dyskinesia",
    r"pulmonary fibrosis",
    r"interstitial nephritis"
]

async def query_biomcp_dme(disease_name, umls_cui):
    """Attempts to query MyDisease.info via the biomcp MCP server to evaluate DME status."""
    # Fast path: Check if the verbatim disease name itself matches a DME keyword first
    if disease_name:
        for keyword in DME_KEYWORDS:
            if re.search(keyword, disease_name, re.IGNORECASE):
                return True, "Local Match (Regex Match)"

    env_cmd = os.environ.get("BIOMCP_COMMAND")
    env_args_str = os.environ.get("BIOMCP_ARGS")
    
    if env_cmd:
        try:
            env_args = json.loads(env_args_str) if env_args_str else []
        except Exception:
            env_args = env_args_str.split() if env_args_str else []
        commands_to_try = [{"command": env_cmd, "args": env_args}]
    else:
        commands_to_try = [
            {"command": "uv", "args": ["run", "--with", "biomcp-python", "python3", "-m", "biomcp", "run"]},
            {"command": "python3", "args": ["-m", "biomcp", "run"]},
            {"command": "biomcp", "args": ["serve"]}
        ]
    
    query_term = umls_cui if umls_cui else disease_name
    if not query_term:
        return False, "None"
        
    for cmd in commands_to_try:
        try:
            server_params = StdioServerParameters(
                command=cmd["command"],
                args=cmd["args"],
                env=os.environ.copy()
            )
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # Call disease_getter tool
                    response = await session.call_tool(
                        "disease_getter",
                        {"disease_id_or_name": query_term}
                    )
                    
                    if response.content:
                        result_text = response.content[0].text
                        # Check if it was a NOT_FOUND message
                        if "not found" in result_text.lower() and umls_cui and disease_name:
                            # Try again using verbatim disease name if CUI query failed
                            response = await session.call_tool(
                                "disease_getter",
                                {"disease_id_or_name": disease_name}
                            )
                            if response.content:
                                result_text = response.content[0].text
                                
                        # Check the returned text against our DME keywords
                        for keyword in DME_KEYWORDS:
                            if re.search(keyword, result_text, re.IGNORECASE):
                                return True, "biomcp / MyDisease.info (Ontology match)"
                                
                        return False, "biomcp / MyDisease.info"
        except Exception:
            continue
            
    # Final fallback if biomcp is unavailable
    if disease_name:
        for keyword in DME_KEYWORDS:
            if re.search(keyword, disease_name, re.IGNORECASE):
                return True, "Local Fallback (Regex Match)"
                
    return False, "None (biomcp offline/unresolved)"

async def process_step4_5(input_data):
    target_events = []

    # 1. Handle target_event input schema
    if "target_event" in input_data:
        target_events.append(input_data["target_event"])
    # 2. Handle umls_profiles list input schema
    elif "umls_profiles" in input_data:
        for profile in input_data["umls_profiles"]:
            syns = profile.get("synonyms", [])
            disease_name = syns[0] if isinstance(syns, list) and syns else ""
            if not disease_name:
                mesh = profile.get("crosswalks", {}).get("mesh_terms", [])
                disease_name = mesh[0] if isinstance(mesh, list) and mesh else ""
            
            target_events.append({
                "verbatim_chunk": disease_name,
                "umls_cui": profile.get("umls_cui", ""),
                "is_negated": False,
                "is_historical": False
            })
    # 3. Handle list of profiles input directly
    elif isinstance(input_data, list):
        for profile in input_data:
            syns = profile.get("synonyms", [])
            disease_name = syns[0] if isinstance(syns, list) and syns else ""
            target_events.append({
                "verbatim_chunk": disease_name,
                "umls_cui": profile.get("umls_cui", ""),
                "is_negated": False,
                "is_historical": False
            })
    else:
        # 4. Handle direct single profile structure
        syns = input_data.get("synonyms", [])
        disease_name = syns[0] if isinstance(syns, list) and syns else ""
        target_events.append({
            "verbatim_chunk": disease_name,
            "umls_cui": input_data.get("umls_cui", ""),
            "is_negated": False,
            "is_historical": False
        })

    is_serious = False
    is_dme = False
    criteria_met = []
    justification_parts = []
    sources = []
    results = []

    for event in target_events:
        verbatim_chunk = event.get("verbatim_chunk", "")
        umls_cui = event.get("umls_cui", "")
        is_negated = event.get("is_negated", False)
        is_historical = event.get("is_historical", False)

        if is_negated or is_historical:
            results.append({
                "umls_cui": umls_cui,
                "is_serious": False,
                "is_designated_medical_event": False,
                "justification_snippet": f"Event '{verbatim_chunk}' is excluded because is_negated={is_negated} or is_historical={is_historical}."
            })
            continue

        cui_is_dme, cui_source = await query_biomcp_dme(verbatim_chunk, umls_cui)
        if cui_is_dme:
            is_serious = True
            is_dme = True
            justification_parts.append(f"Designated Medical Event identified: '{verbatim_chunk}' ({umls_cui}) via {cui_source}.")
        else:
            justification_parts.append(f"No Designated Medical Event detected for: '{verbatim_chunk}' ({umls_cui}).")

        results.append({
            "umls_cui": umls_cui,
            "is_serious": cui_is_dme,
            "is_designated_medical_event": cui_is_dme,
            "justification_snippet": f"Designated Medical Event identified: '{verbatim_chunk}'." if cui_is_dme else "No Designated Medical Event detected.",
            "dme_ontology_source": cui_source
        })
        sources.append(cui_source)

    if is_dme:
        criteria_met = ["Important Medical Event (IME)"]

    justification_snippet = " ".join(justification_parts) if justification_parts else "No events to evaluate."
    dme_source = ", ".join(set(sources)) if sources else "None"

    return {
        "is_serious": is_serious,
        "seriousness_criteria_met": criteria_met,
        "is_designated_medical_event": is_dme,
        "provenance_receipts": {
            "justification_snippet": justification_snippet,
            "dme_ontology_source": dme_source
        },
        "evaluated_events": results
    }

async def main():
    input_text = None
    if len(sys.argv) > 1:
        input_text = sys.argv[1].strip()
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
        
    if not input_text:
        sys.stderr.write("Error: No input JSON payload provided.\n")
        sys.exit(1)
        
    try:
        input_data = json.loads(input_text)
    except Exception as e:
        sys.stderr.write(f"Error parsing input JSON: {e}\n")
        sys.exit(1)
        
    output = await process_step4_5(input_data)
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
