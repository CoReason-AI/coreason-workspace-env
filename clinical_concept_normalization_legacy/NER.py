import contextlib
import json
import sys
from typing import Any

import medspacy
import spacy

# Local Heuristics & Filters (Fully deterministic local execution matching NER.md)
STOP_WORDS_CLINICAL = {
    "he",
    "she",
    "it",
    "they",
    "this",
    "that",
    "there",
    "here",
    "but",
    "and",
    "or",
    "a",
    "an",
    "the",
    "has",
    "have",
    "had",
    "with",
    "without",
    "no",
    "denies",
    "but has",
    "but has a",
    "to the",
    "prior to",
    "of",
    "at",
    "in",
    "on",
    "any",
    "complaining",
    "complaining of",
    "complains",
    "arrived",
    "admission",
    "prior",
    "admitted",
    "discharge",
    "discharged",
    "presents",
    "presenting",
    "shows",
    "showed",
    "reveals",
    "revealed",
    "evidence",
    "exam",
    "examination",
    "assessment",
    "plan",
    "discussion",
    "results",
    "labs",
    "laboratory",
    "history",
    "history of",
    "severe",
    "mild",
    "moderate",
    "acute",
    "chronic",
    "significant",
    "marked",
    "evidence of",
    "significant for",
    "patient",
    "patients",
    "symptoms",
    "symptom",
    "relief",
    "relief of",
    "use",
    "tablets",
    "tablet",
    "capsules",
    "capsule",
    "pills",
    "pill",
    "sl",
    "sublingual",
    "po",
    "iv",
    "im",
    "prn",
    "qd",
    "bid",
    "tid",
    "qid",
    "mg",
    "ml",
    "g",
    "dose",
    "doses",
    "emergency department",
    "ed",
    "er",
    "hospital",
    "clinic",
    "department",
    "type 2",
    "type 1",
    "type",
    "2",
    "1",
    "3",
    "4",
    "5",
    "co",
    "physical exam",
}

EXCLUDED_WEB_LABELS = {
    "CARDINAL",
    "QUANTITY",
    "DATE",
    "TIME",
    "ORDINAL",
    "PERCENT",
    "MONEY",
    "LAW",
    "LANGUAGE",
    "WORK_OF_ART",
    "EVENT",
    "PRODUCT",
    "LOC",
    "GPE",
    "ORG",
    "FAC",
    "NORP",
    "PERSON",
}

# Clinical concept routes and abbreviations to filter out
CLINICAL_ABBR_BLACKLIST = {"bid", "sl", "qd", "tid", "qid", "po", "iv", "im", "prn", "mg", "ml"}

CONCEPT_TYPE_MAPPING = {
    "DISEASE": "Disease/Symptom",
    "CHEMICAL": "Drug/Chemical",
    "SIMPLE_CHEMICAL": "Drug/Chemical",
    "CANCER": "Disease/Symptom",
    "PATHOLOGICAL_FORMATION": "Disease/Symptom",
    "GENE_OR_GENE_PRODUCT": "Gene/Protein",
    "ANATOMICAL_SYSTEM": "Anatomy",
    "ORGAN": "Anatomy",
    "TISSUE": "Anatomy",
    "CELL": "Anatomy",
    "CELLULAR_COMPONENT": "Anatomy",
    "DEVELOPING_ANATOMICAL_STRUCTURE": "Anatomy",
    "IMMATERIAL_ANATOMICAL_ENTITY": "Anatomy",
    "MULTI_TISSUE_STRUCTURE": "Anatomy",
    "ENTITY": "Clinical Concept",
    "ORGANISM": "Organism/Species",
}


def load_chunker_pipeline() -> tuple[Any, Any]:
    """Initializes and stacks all four requested models with MedSpaCy components."""
    try:
        nlp = medspacy.load("en_ner_bc5cdr_md", medspacy_enable=["medspacy_sectionizer", "medspacy_context"])
        nlp_bionlp = spacy.load("en_ner_bionlp13cg_md")
        nlp_core = spacy.load("en_core_sci_md")
        nlp_web = spacy.load("en_core_web_md")

        nlp.add_pipe("ner", source=nlp_bionlp, name="ner_bionlp", before="medspacy_context")
        nlp.add_pipe("ner", source=nlp_core, name="ner_core", before="medspacy_context")

        return nlp, nlp_web
    except Exception as e:
        sys.stderr.write(f"Fatal error loading pipeline: {e}\n")
        sys.exit(1)


def get_provenance_snippet(text: str, start_char: int, end_char: int) -> str:
    """Generates a 5-7 word snippet citation surrounding the extracted entity."""
    words_before = text[:start_char].strip().split()
    words_after = text[end_char:].strip().split()
    entity_words = text[start_char:end_char].strip().split()

    n_entity = len(entity_words)
    needed = max(0, 6 - n_entity)
    before_count = needed // 2
    after_count = needed - before_count

    snippet_words = words_before[-before_count:] if before_count > 0 else []
    snippet_words += entity_words
    snippet_words += words_after[:after_count] if after_count > 0 else []

    return " ".join(snippet_words)


def generate_reasoning_trace(mention: str, label: str, is_negated: bool, is_historical: bool) -> str:
    """Programmatically constructs a detailed reasoning monologue for the deterministic output."""
    negation_reason = (
        "evaluated as NEGATED due to a syntactic negation trigger "
        "(e.g., 'denies', 'no', 'without') identified in its context window"
        if is_negated
        else "evaluated as AFFIRMED because no negation triggers or syntactic "
        "negation modifiers were found in its context window"
    )
    history_reason = (
        "evaluated as HISTORICAL/FAMILY because it occurs within a history section "
        "or possesses historical/temporal indicators"
        if is_historical
        else "evaluated as CURRENT/PATIENT because it has no markers indicating "
        "family history or a historical/past event"
    )
    return (
        f"Extracted verbatim clinical concept '{mention}' of type '{label}'. "
        f"The assertion status is {negation_reason}. "
        f"The temporal context is {history_reason}."
    )


def process_ner_chunking(input_payload: dict[str, Any], nlp: Any, nlp_web: Any) -> dict[str, Any]:
    """Processes normalized clinical text and compiles it into the NERChunkData schema."""
    text = input_payload.get("normalized_text")
    if not text or not text.strip():
        return {"error": "INSUFFICIENT_DATA", "message": "Input normalized_text is empty or not provided."}

    doc = nlp(text)
    doc_web = nlp_web(text)

    # Gather all entities from both pipelines
    raw_ents = list(doc.ents)
    seen_spans = {(e.start_char, e.end_char) for e in raw_ents}
    for e_web in doc_web.ents:
        if (e_web.start_char, e_web.end_char) not in seen_spans:
            raw_ents.append(e_web)
            seen_spans.add((e_web.start_char, e_web.end_char))

    # Step 1: Filter out non-clinical entities, grammar noise, and stopwords
    filtered_ents = []
    for ent in raw_ents:
        cleaned_text = ent.text.strip().lower().rstrip(".,;: ")

        # Apply standard blacklist filters
        if cleaned_text in STOP_WORDS_CLINICAL:
            continue
        if ent.label_ in EXCLUDED_WEB_LABELS:
            continue
        if len(cleaned_text) <= 1 and not cleaned_text.isalnum():
            continue

        # Fallback local syntactic parser check (Alternative 1 & 2)
        if ent.root.pos_ not in {"NOUN", "PROPN"} and ent.root.dep_ not in {"compound", "nsubj", "dobj", "pobj"}:
            continue
        if ent.root.is_stop or cleaned_text in nlp.Defaults.stop_words:
            continue
        if cleaned_text in CLINICAL_ABBR_BLACKLIST:
            continue

        filtered_ents.append(ent)

    # Step 2: Resolve overlapping entity spans (longer spans take priority)
    filtered_ents = sorted(filtered_ents, key=lambda x: x.end_char - x.start_char, reverse=True)
    consolidated_ents: list[Any] = []

    for ent in filtered_ents:
        overlaps = False
        for existing in consolidated_ents:
            if ent.start_char < existing.end_char and ent.end_char > existing.start_char:
                overlaps = True
                break
        if not overlaps:
            consolidated_ents.append(ent)

    # Sort consolidated entities back by start character offset for sequential output
    consolidated_ents = sorted(consolidated_ents, key=lambda x: x.start_char)

    # Refusal predicate: If no clinical entities are found, return failure status
    if not consolidated_ents:
        return {"error": "NOT_FOUND", "message": "No clinical entities were detected in the input text."}

    clinical_chunks = []
    provenance_receipts = []

    for ent in consolidated_ents:
        # Determine assertions via MedSpaCy attributes
        is_negated = getattr(ent._, "is_negated", False)
        is_historical = getattr(ent._, "is_historical", False)

        # Map raw label to clean concept type
        concept_type = CONCEPT_TYPE_MAPPING.get(ent.label_, "Clinical Concept")

        # Build components
        trace = generate_reasoning_trace(ent.text, concept_type, is_negated, is_historical)
        citation = get_provenance_snippet(text, ent.start_char, ent.end_char)

        clinical_chunks.append(
            {
                "reasoning_trace": trace,
                "verbatim_chunk": ent.text,
                "concept_type": concept_type,
                "is_negated": is_negated,
                "is_historical": is_historical,
            }
        )

        provenance_receipts.append({"chunk": ent.text, "source_snippet_citation": citation})

    return {"clinical_chunks": clinical_chunks, "provenance_receipts": provenance_receipts}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clinical NER Chunker mapping to NER.md schema.")
    parser.add_argument("text", nargs="*", help="The normalized clinical text to analyze.")
    args = parser.parse_args()

    # Retrieve input text from arguments, stdin, or fallback to sample
    if args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        text = "Patient denies myocardial infarction but has a past medical history of asthma."
        sys.stderr.write(f'No input text provided. Running with sample text: "{text}"\n\n')

    nlp, nlp_web = load_chunker_pipeline()

    # Handle JSON inputs (robustly extracting JSON if nested within output traces/logs)
    input_payload = None

    # 1. Attempt direct full parse
    with contextlib.suppress(Exception):
        input_payload = json.loads(text)

    # 2. Attempt extracting from markdown block
    if not input_payload and "```json" in text:
        try:
            parts = text.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0].strip()
                input_payload = json.loads(json_part)
        except Exception:
            pass

    # 3. Attempt finding first '{' and last '}'
    if not input_payload:
        try:
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_candidate = text[start_idx : end_idx + 1]
                input_payload = json.loads(json_candidate)
        except Exception:
            pass

    # 4. Fallback to raw text
    if not input_payload:
        input_payload = {"normalized_text": text}

    # Extract only the normalized_text field if a dictionary is resolved
    if isinstance(input_payload, dict):
        normalized_val = input_payload.get("normalized_text", text)
        input_payload = {"normalized_text": normalized_val}

    output = process_ner_chunking(input_payload, nlp, nlp_web)
    print(json.dumps(output, indent=2))
