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
