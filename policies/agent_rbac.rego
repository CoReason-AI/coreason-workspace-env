package coreason.authz

default allow = false

# Allow all actions if the agent is the factory_ceo
allow {
    input.agent == "factory_ceo"
}

# Allow yaml_compiler to write only .yaml files
allow {
    input.agent == "yaml_compiler"
    input.tool == "write_file"
    endswith(input.payload.kwargs.file_path, ".yaml")
}

# Allow librarian_pm to use extract_and_read_context tool
allow {
    input.agent == "librarian_pm"
    input.tool == "extract_and_read_context"
}

# Deny everything else by default
