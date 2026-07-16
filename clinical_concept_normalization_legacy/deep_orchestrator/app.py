import os
import sys

# Force Python to use the modern local deepagents SDK instead of the outdated Anaconda version
sys.path.insert(0, "/home/ubuntu/Documents/testing/deepagents/libs/deepagents")

import json
import shutil
import traceback
import streamlit as st
from pydantic import create_model

from deep_orchestrator import SwarmOrchestrator

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Deep Agent Studio", layout="wide")

# --- Load API Keys from .env ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split('=', 1)
                os.environ[key] = val.strip('"\'')
# -------------------------------

# Setup temporary directories for dynamic file generation
TEMP_DIR = "/tmp/deepagent_studio"
SKILLS_DIR = os.path.join(TEMP_DIR, "skills", "dynamic_skill")
MEMORY_DIR = os.path.join(TEMP_DIR, "memory")

def ensure_temp_dirs():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(SKILLS_DIR)
    os.makedirs(MEMORY_DIR)

BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "saved_blueprints")
AGENTS_DIR = os.path.join(BLUEPRINTS_DIR, "agents")
SCRIPTS_DIR = os.path.join(BLUEPRINTS_DIR, "scripts")

def ensure_blueprint_dirs():
    os.makedirs(AGENTS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

ensure_blueprint_dirs()

# Initialize Session State by loading from permanent disk storage
if "saved_agents" not in st.session_state:
    st.session_state.saved_agents = {}
    for filename in os.listdir(AGENTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(AGENTS_DIR, filename), "r") as f:
                name = filename.replace(".json", "")
                st.session_state.saved_agents[name] = json.load(f)

if "saved_scripts" not in st.session_state:
    st.session_state.saved_scripts = {}
    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith(".py"):
            with open(os.path.join(SCRIPTS_DIR, filename), "r") as f:
                name = filename.replace(".py", "")
                st.session_state.saved_scripts[name] = f.read()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🤖 Deep Agent Builder", "🐍 Python Script Node", "🔗 Workflow Orchestrator"])

# ==========================================
# PAGE 1: DEEP AGENT BUILDER
# ==========================================
if page == "🤖 Deep Agent Builder":
    st.title("🤖 Deep Agent Builder")
    st.markdown("Configure a Deep Agent and save it to the workspace.")
    
    existing_agents = list(st.session_state.saved_agents.keys())
    selected_agent = st.selectbox("Load Existing Agent (or Create New)", ["-- Create New --"] + existing_agents)
    
    if selected_agent != "-- Create New --":
        loaded_cfg = st.session_state.saved_agents[selected_agent]
        def_name = selected_agent
        def_provider = loaded_cfg["provider"]
        def_model_name = loaded_cfg["model"].split(":")[1] if ":" in loaded_cfg["model"] else loaded_cfg["model"]
        def_sp_prefix = loaded_cfg["sp_prefix"]
        def_sp_suffix = loaded_cfg["sp_suffix"]
        def_use_json = loaded_cfg["use_json"]
        def_response_schema_str = loaded_cfg["response_schema_str"]
        def_memory_content = loaded_cfg["memory_content"]
        def_skill_contents = loaded_cfg["skill_contents"] if loaded_cfg["skill_contents"] else [""]
        def_rubric_content = loaded_cfg.get("rubric_content", "")
        def_temperature = loaded_cfg["temperature"]
        def_debug = loaded_cfg["debug"]
    else:
        def_name = "ClinicalSynthesizer"
        def_provider = "openai"
        def_model_name = "gpt-4o"
        def_sp_prefix = "You are a helpful agent."
        def_sp_suffix = ""
        def_use_json = False
        def_response_schema_str = '{\n  "title": "Output",\n  "type": "object",\n  "properties": {\n    "result": {"type": "string"}\n  }\n}'
        def_memory_content = ""
        def_skill_contents = [""]
        def_rubric_content = ""
        def_temperature = 0.0
        def_debug = True
        
    agent_name = st.text_input("Agent Node Name", value=def_name)
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("1. Core Configuration")
        provider_options = ["openai", "anthropic", "deepseek", "google"]
        provider_idx = provider_options.index(def_provider) if def_provider in provider_options else 0
        provider = st.selectbox("Model Provider", provider_options, index=provider_idx)
        
        if provider == "openai":
            model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        elif provider == "anthropic":
            model_options = ["claude-3-5-sonnet-latest", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        elif provider == "deepseek":
            model_options = ["deepseek-chat", "deepseek-coder", "deepseek-v4-flash"]
        elif provider == "google":
            model_options = ["gemini-1.5-pro", "gemini-1.5-flash"]
            
        model_idx = model_options.index(def_model_name) if def_model_name in model_options else 0
        model_name = st.selectbox("Model Name", model_options, index=model_idx)
            
        model = f"{provider}:{model_name}"
        
        st.subheader("System Prompt (Config)")
        sp_prefix = st.text_area("Prefix (Top Priority)", value=def_sp_prefix, height=150)
        sp_suffix = st.text_area("Suffix (Closing Constraints)", value=def_sp_suffix, height=150)
        
        st.subheader("Structured Output (Response Format)")
        use_json = st.checkbox("Enforce JSON Output Schema?", value=def_use_json)
        response_schema_str = st.text_area(
            "JSON Schema (Valid JSON Schema)", 
            value=def_response_schema_str,
            disabled=not use_json,
            height=200
        )

    with col2:
        st.header("2. Environment & Harness")
        
        st.subheader("Memory Content")
        memory_content = st.text_area("Persistent Memory", value=def_memory_content, height=100)
        
        st.subheader("Skill Contents (Multi-Skill)")
        st.markdown("Deep Agents can hold multiple skills in its memory and dynamically select the right one based on the YAML description!")
        
        num_skills = st.number_input("Number of Skills for this Agent", min_value=1, max_value=5, value=max(1, len(def_skill_contents)), step=1)
        skill_contents = []
        for i in range(num_skills):
            sk_val = def_skill_contents[i] if i < len(def_skill_contents) else ""
            skill_contents.append(
                st.text_area(f"Skill ##{i+1} (Include YAML frontmatter)", value=sk_val, height=150, key=f"skill_{i}_{agent_name}")
            )
        
        st.subheader("Execution Settings")
        rubric_content = st.text_area("Quality Rubric (Leave blank to disable)", value=def_rubric_content, height=100)
        temperature = st.slider("Model Temperature (0.0 = Consistent, 1.0 = Creative)", min_value=0.0, max_value=1.0, value=def_temperature, step=0.1)
        debug_mode = st.checkbox("Enable Debug Mode", value=def_debug)

    if st.button("Save Deep Agent to Workspace", type="primary", use_container_width=True):
        config_data = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "sp_prefix": sp_prefix,
            "sp_suffix": sp_suffix,
            "use_json": use_json,
            "response_schema_str": response_schema_str,
            "memory_content": memory_content,
            "skill_contents": [s for s in skill_contents if s.strip()],
            "rubric_content": rubric_content,
            "debug": debug_mode
        }
        st.session_state.saved_agents[agent_name] = config_data
        
        # Permanent Save to Disk
        with open(os.path.join(AGENTS_DIR, f"{agent_name}.json"), "w") as f:
            json.dump(config_data, f, indent=4)
            
        st.success(f"✅ Agent '{agent_name}' permanently saved to the orchestrator workspace!")

# ==========================================
# PAGE 2: PYTHON SCRIPT NODE
# ==========================================
elif page == "🐍 Python Script Node":
    st.title("🐍 Python Script Node Builder")
    st.markdown("Write a deterministic Python script to act as a node in the graph. The script must define a function called `process(state)`.")
    
    existing_scripts = list(st.session_state.saved_scripts.keys())
    selected_script = st.selectbox("Load Existing Script (or Create New)", ["-- Create New --"] + existing_scripts)
    
    if selected_script != "-- Create New --":
        def_script_name = selected_script
        def_script_code = st.session_state.saved_scripts[selected_script]
    else:
        def_script_name = "DeterministicNormalizer"
        def_script_code = """def process(state):
    \"\"\"
    A standard LangGraph node function.
    It receives the GlobalSwarmState dict and must return a state update dict.
    \"\"\"
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        print(f"Script {script_name} received: {last_message}")
        
    return {"messages": [("assistant", "Processed by Python script.")]}
"""
    
    script_name = st.text_input("Script Node Name", value=def_script_name)
    
    script_code = st.text_area("Python Code", value=def_script_code, height=400)
    
    if st.button("Save Script Node to Workspace", type="primary", use_container_width=True):
        st.session_state.saved_scripts[script_name] = script_code
        
        # Permanent Save to Disk
        with open(os.path.join(SCRIPTS_DIR, f"{script_name}.py"), "w") as f:
            f.write(script_code)
            
        st.success(f"✅ Python Script '{script_name}' permanently saved to the orchestrator workspace!")

# ==========================================
# PAGE 3: WORKFLOW ORCHESTRATOR
# ==========================================
elif page == "🔗 Workflow Orchestrator":
    st.title("🔗 Workflow Orchestrator")
    st.markdown("Connect your Deep Agents and Python Scripts into a multi-node Swarm.")
    
    all_nodes = list(st.session_state.saved_agents.keys()) + list(st.session_state.saved_scripts.keys())
    
    if not all_nodes:
        st.warning("No agents or scripts saved yet. Go back to the builders to add nodes to the workspace!")
    else:
        st.info(f"**Available Nodes in Workspace:** {', '.join(all_nodes)}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("Graph Routing")
            entry_point = st.selectbox("Select Entry Point Node", all_nodes)
            
            st.subheader("Connections (Sequential Edges)")
            num_edges = st.number_input("Number of Edges", min_value=0, value=0, step=1)
            
            edges = []
            for i in range(num_edges):
                c_from, c_to = st.columns(2)
                frm = c_from.selectbox(f"From ##{i+1}", all_nodes, key=f"from_{i}")
                to = c_to.selectbox(f"To ##{i+1}", all_nodes, key=f"to_{i}")
                edges.append((frm, to))
                
        with col2:
            st.header("Execution")
            
            # Checkpointer Thread ID
            thread_id = st.text_input("Thread ID (For Memory Persistence across runs)", value="thread_1")
            
            user_query = st.text_area("Initial User Query (Payload):", height=150)
            
            if st.button("Compile & Run Workflow", type="primary", use_container_width=True):
                if not user_query:
                    st.warning("Please provide a user query.")
                else:
                    with st.spinner("Compiling multi-agent graph and executing..."):
                        try:
                            ensure_temp_dirs()
                            swarm = SwarmOrchestrator()
                            
                            # 1. Load all Deep Agents
                            for name, config in st.session_state.saved_agents.items():
                                memory_path = os.path.join(MEMORY_DIR, f"{name}_memory.md")
                                if config["memory_content"].strip():
                                    with open(memory_path, "w") as f:
                                        f.write(config["memory_content"])
                                
                                # Write multiple skills to the Skills Directory
                                agent_skill_dir = os.path.join(SKILLS_DIR, name)
                                if not os.path.exists(agent_skill_dir):
                                    os.makedirs(agent_skill_dir)
                                    
                                has_skills = False
                                for idx, skill_text in enumerate(config.get("skill_contents", [])):
                                    if skill_text.strip():
                                        skill_path = os.path.join(agent_skill_dir, f"skill_{idx}.md")
                                        with open(skill_path, "w") as f:
                                            f.write(skill_text)
                                        has_skills = True
                                        
                                system_prompt_config = {"prefix": config["sp_prefix"], "base": None}
                                if config["sp_suffix"].strip(): system_prompt_config["suffix"] = config["sp_suffix"]
                                
                                response_format = None
                                if config["use_json"] and config["response_schema_str"].strip():
                                    response_format = json.loads(config["response_schema_str"])
                                    
                                from langchain.chat_models import init_chat_model
                                if config["provider"] in ["deepseek", "openai"]:
                                    active_model = init_chat_model(config["model"], temperature=config["temperature"], use_responses_api=False)
                                else:
                                    active_model = init_chat_model(config["model"], temperature=config["temperature"])
                                    
                                agent_middlewares = []
                                if config.get("rubric_content", "").strip():
                                    from deepagents.middleware import RubricMiddleware
                                    agent_middlewares.append(
                                        RubricMiddleware(
                                            model=active_model,
                                            max_iterations=3
                                        )
                                    )
                                    
                                swarm.add_reasoning_agent(
                                    name=name,
                                    model=active_model,
                                    system_prompt=system_prompt_config,
                                    memory=[memory_path] if config["memory_content"].strip() else None,
                                    skills=[agent_skill_dir] if has_skills else None,
                                    response_format=response_format,
                                    middleware=agent_middlewares,
                                    debug=config["debug"]
                                )
                                
                            # 2. Load all Python Script Nodes
                            for name, code in st.session_state.saved_scripts.items():
                                local_env = {}
                                exec(code, globals(), local_env)
                                if "process" not in local_env:
                                    raise ValueError(f"Script node '{name}' must define a 'process(state)' function.")
                                swarm.add_script_agent(name, local_env["process"])
                                
                            # 3. Connect Graph
                            swarm.set_entry_point(entry_point)
                            for frm, to in edges:
                                swarm.add_peer_connection(frm, to)
                                
                            from langgraph.checkpoint.memory import MemorySaver
                            if "checkpointer" not in st.session_state:
                                st.session_state.checkpointer = MemorySaver()
                            app = swarm.compile(checkpointer=st.session_state.checkpointer)
                            
                            # Invoke with thread config
                            st.subheader("Live Agent Logs")
                            log_container = st.container()
                            
                            from langchain_core.callbacks import BaseCallbackHandler
                            class StreamlitContextHandler(BaseCallbackHandler):
                                def __init__(self, container):
                                    self.container = container
                                    
                                def on_chat_model_start(self, serialized, messages, **kwargs):
                                    with self.container.expander("🔍 RAW AI CONTEXT WINDOW [llm/start]", expanded=False):
                                        for msg in messages[0]:
                                            msg_type = getattr(msg, "type", "unknown")
                                            content = getattr(msg, "content", str(msg))
                                            st.markdown(f"**{msg_type.upper()} MESSAGE**")
                                            st.code(content, language="markdown")
                                            
                                def on_tool_start(self, serialized, input_str, **kwargs):
                                    tool_name = serialized.get("name", "tool")
                                    with self.container.expander(f"🛠️ TOOL EXECUTION [{tool_name}]", expanded=False):
                                        st.code(input_str, language="json")

                            invoke_config = {
                                "configurable": {"thread_id": thread_id},
                                "callbacks": [StreamlitContextHandler(log_container)]
                            }
                            
                            # Inject the rubric into initial state if present
                            initial_state = {"messages": [("user", user_query)]}
                            for name, config in st.session_state.saved_agents.items():
                                if config.get("rubric_content", "").strip():
                                    initial_state["rubric"] = config["rubric_content"]
                                    break
                                    
                            result = app.invoke(initial_state, invoke_config)
                            
                            st.success("Workflow Execution Complete!")
                            
                            # Show Step-by-Step Trajectory
                            st.subheader("Agent Trajectory (Step-by-Step)")
                            messages = result.get("messages", [])
                            
                            for i, msg in enumerate(messages):
                                msg_type = getattr(msg, "type", "unknown")
                                
                                # Default to expanding only the intermediate AI/Tool steps, keep Human/Final closed
                                is_expanded = (msg_type not in ["human"])
                                
                                with st.expander(f"Step {i+1}: {msg_type.upper()}", expanded=is_expanded):
                                    # Show if it's a structured tool call
                                    if getattr(msg, "tool_calls", None):
                                        st.markdown("**Tool Call Requested:**")
                                        for tool in msg.tool_calls:
                                            st.write(f"🛠️ `{tool.get('name')}`")
                                            st.json(tool.get("args", {}))
                                            
                                    # Show text content if it exists
                                    content = getattr(msg, "content", "").strip()
                                    if content:
                                        # If the content looks like JSON, render it nicely
                                        try:
                                            parsed_json = json.loads(content)
                                            st.markdown("**Output Content:**")
                                            st.json(parsed_json)
                                        except:
                                            st.markdown("**Output Content:**")
                                            st.markdown(content)
                            
                            # Show Final Output
                            st.subheader("🎯 Final Structured Output")
                            final_output = None
                            for msg in reversed(messages):
                                if getattr(msg, "type", "") == "ai" and getattr(msg, "tool_calls", None):
                                    final_output = msg.tool_calls[0].get("args")
                                    break
                                if getattr(msg, "type", "") == "ai" and getattr(msg, "content", "").strip():
                                    final_output = msg.content
                                    break
                                    
                            if final_output:
                                if isinstance(final_output, dict):
                                    st.json(final_output)
                                else:
                                    st.markdown(final_output)
                            else:
                                st.warning("No explicit output extracted.")
                                
                            with st.expander("View Full Raw State", expanded=False):
                                st.write(result)
                                
                        except Exception as e:
                            st.error("Error during workflow execution:")
                            st.code(traceback.format_exc(), language="text")
