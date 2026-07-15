import os
import yaml

def test_cloudformation_template_exists_and_valid():
    """
    E2E No Mock Test: Validate the structural integrity of the CloudFormation template
    and ensure it aligns with the expected docker images.
    """
    cfn_path = os.path.join(os.getcwd(), "deploy", "cloudformation", "coreason-enterprise.yaml")
    assert os.path.exists(cfn_path), "CloudFormation template must exist"
    
    class CFNSafeLoader(yaml.SafeLoader):
        pass

    def construct_undefined(self, node):
        return node.value

    CFNSafeLoader.add_constructor('!Ref', construct_undefined)
    CFNSafeLoader.add_multi_constructor('!', construct_undefined)
    
    with open(cfn_path, "r", encoding="utf-8") as f:
        template = yaml.load(f, Loader=CFNSafeLoader)
        
    assert "Resources" in template
    assert "PlatformTaskDefinition" in template["Resources"]
    
    task_def = template["Resources"]["PlatformTaskDefinition"]["Properties"]
    containers = task_def["ContainerDefinitions"]
    assert len(containers) > 0
    assert "ghcr.io/coreason-ai/coreason-workspace-env" in containers[0]["Image"]

def test_github_actions_workflow_exists_and_valid():
    """
    E2E No Mock Test: Validate the structural integrity of the GitHub Actions workflow.
    """
    workflow_path = os.path.join(os.getcwd(), ".github", "workflows", "deploy-helm.yml")
    assert os.path.exists(workflow_path), "GitHub Actions workflow must exist"
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = yaml.safe_load(f)
        
    assert "jobs" in workflow
    assert "deploy" in workflow["jobs"]
    assert "steps" in workflow["jobs"]["deploy"]
    
    # Check that helm upgrade is called
    steps = workflow["jobs"]["deploy"]["steps"]
    helm_step = next((step for step in steps if "helm upgrade" in step.get("run", "")), None)
    assert helm_step is not None, "Helm deployment step must exist"

def test_terraform_modules_exist():
    """
    Verify Terraform modules exist for both AWS and Azure.
    """
    aws_dir = os.path.join(os.getcwd(), "deploy", "terraform", "aws")
    azure_dir = os.path.join(os.getcwd(), "deploy", "terraform", "azure")
    
    assert os.path.exists(os.path.join(aws_dir, "main.tf"))
    assert os.path.exists(os.path.join(aws_dir, "variables.tf"))
    assert os.path.exists(os.path.join(aws_dir, "outputs.tf"))
    
    assert os.path.exists(os.path.join(azure_dir, "main.tf"))
    assert os.path.exists(os.path.join(azure_dir, "variables.tf"))
    assert os.path.exists(os.path.join(azure_dir, "outputs.tf"))

if __name__ == "__main__":
    test_cloudformation_template_exists_and_valid()
    test_github_actions_workflow_exists_and_valid()
    test_terraform_modules_exist()
    print("Marketplace structural tests passed.")
