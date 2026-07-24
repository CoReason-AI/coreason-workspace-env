import pytest
from src.core.services.skill_service import skill_service

def test_skill_service_list():
    skills = skill_service.list_skills()
    assert isinstance(skills, list)
    assert len(skills) > 0
    
    # Verify mandatory categories
    categories = {s["category"] for s in skills}
    assert "building" in categories or "validation" in categories

def test_skill_service_get():
    skills = skill_service.list_skills()
    first_skill = skills[0]
    
    fetched = skill_service.get_skill(first_skill["name"])
    assert fetched is not None
    assert fetched["name"] == first_skill["name"]
    assert "content" in fetched
    assert len(fetched["content"]) > 0

def test_skill_service_validation():
    skills = skill_service.list_skills()
    real_name = skills[0]["name"]
    
    res = skill_service.validate_skill_references([real_name, "non_existent_skill_xyz"])
    assert res["is_valid"] is False
    assert len(res["valid"]) == 1
    assert "non_existent_skill_xyz" in res["missing"]


def test_forge_and_clone_skill():
    # 1. Forge skill
    res = skill_service.forge_skill(
        skill_id="sec_filing_analysis_skill",
        name="SEC Filing Analysis",
        category="building",
        description="Analyzes SEC 10-K filings for risk factors",
        content="## SEC Filing Analysis Protocol\n1. Extract Item 1A Risk Factors.\n2. Run sentiment analysis.",
        tags=["sec", "finance"]
    )
    assert res["status"] == "success"
    assert res["skill_id"] == "sec_filing_analysis_skill"
    assert "urn:oid:1.3.6.1.4.1.66197:skill:sec_filing_analysis_skill" in res["urn"]

    # 2. Clone skill
    cloned = skill_service.clone_skill("urn:oid:1.3.6.1.4.1.66197:skill:sec_filing_analysis_skill", target_category="cloned")
    assert cloned["status"] == "success"
    assert cloned["path"] == "cloned/sec_filing_analysis_skill.md"

