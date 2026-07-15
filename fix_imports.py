import os
import glob

def fix_imports():
    files = glob.glob('c:/files/git/github/coreason-ai/coreason-workspace-env/src/agents/**/*.py', recursive=True)
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'from deepagents import DeepAgent' in content:
            new_content = content.replace('from deepagents import DeepAgent', 'from deepagents import SubAgent as DeepAgent')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f'Fixed {f}')

fix_imports()
