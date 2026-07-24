"""
Central LangGraph Tool Registry — Gemini, Antigravity, Claude Code, & Windsurf Capability Matrix.
"""
from src.core.tools.catalog_tools import (
    search_catalog_tool,
    resolve_urn_tool,
    import_catalog_module_tool,
    forge_tool_tool,
    forge_skill_tool,
    clone_skill_tool,
)
from src.core.tools.filesystem_tools import (
    view_file_tool,
    write_file_tool,
    replace_file_content_tool,
    grep_search_tool,
    list_dir_tool,
)
from src.core.tools.audit_testing_tools import (
    audit_artifact_tool,
    run_agent_tests_tool,
    improve_artifact_tool,
)
from src.core.tools.reasoning_tools import (
    analogical_mapping_tool,
    neurosymbolic_deduction_tool,
)
from src.core.tools.causal_thought_tools import (
    prove_causal_hypothesis_tool,
    organize_thoughts_tool,
    structure_complex_thoughts_tool,
)

ALL_FACTORY_TOOLS = [
    search_catalog_tool,
    resolve_urn_tool,
    import_catalog_module_tool,
    forge_tool_tool,
    forge_skill_tool,
    clone_skill_tool,
    view_file_tool,
    write_file_tool,
    replace_file_content_tool,
    grep_search_tool,
    list_dir_tool,
    audit_artifact_tool,
    run_agent_tests_tool,
    improve_artifact_tool,
    analogical_mapping_tool,
    neurosymbolic_deduction_tool,
    prove_causal_hypothesis_tool,
    organize_thoughts_tool,
    structure_complex_thoughts_tool,
]
