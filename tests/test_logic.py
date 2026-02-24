"""Test logic evaluator for resume screening."""
import pytest
from src.schemas.condition import (
    ConditionGroup,
    FilterCondition,
    LogicalOperator,
    ComparisonOperator,
)
from src.workflows.filter_node import ConditionEvaluator

class TestConditionEvaluator:
    
    @pytest.fixture
    def candidate_info(self):
        return {
            "name": "Alice",
            "education_level": "master",
            "work_years": 5,
            "skills": ["Python", "Java", "SQL", "Docker"],
            "major": "Computer Science",
            "school": "MIT"
        }

    @pytest.fixture
    def resume_text(self):
        return "Experienced software engineer with expertise in microservices and cloud computing."

    def test_simple_skill_match(self, candidate_info):
        # Condition: Skills CONTAINS Python
        condition = FilterCondition(
            field="skills",
            operator=ComparisonOperator.CONTAINS,
            value="Python"
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(condition) is True

    def test_simple_skill_mismatch(self, candidate_info):
        # Condition: Skills CONTAINS Ruby
        condition = FilterCondition(
            field="skills",
            operator=ComparisonOperator.CONTAINS,
            value="Ruby"
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(condition) is False

    def test_and_logic(self, candidate_info):
        # (Skill Python AND Skill Java)
        group = ConditionGroup(
            operator=LogicalOperator.AND,
            conditions=[
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Python"),
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Java"),
            ]
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(group) is True

    def test_and_logic_fail(self, candidate_info):
        # (Skill Python AND Skill Ruby)
        group = ConditionGroup(
            operator=LogicalOperator.AND,
            conditions=[
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Python"),
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Ruby"),
            ]
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(group) is False

    def test_or_logic(self, candidate_info):
        # (Skill Ruby OR Skill Python)
        group = ConditionGroup(
            operator=LogicalOperator.OR,
            conditions=[
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Ruby"),
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Python"),
            ]
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(group) is True

    def test_nested_logic(self, candidate_info):
        # (Skill Python OR Java) AND (Years >= 3)
        # Note: (A OR B) is Group1. Years>=3 is Condition2.
        # Root Group is AND(Group1, Condition2).
        
        group1 = ConditionGroup(
            operator=LogicalOperator.OR,
            conditions=[
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Python"),
                FilterCondition(field="skills", operator=ComparisonOperator.CONTAINS, value="Java"),
            ]
        )
        cond2 = FilterCondition(field="work_years", operator=ComparisonOperator.GTE, value=3)
        
        root = ConditionGroup(
            operator=LogicalOperator.AND,
            conditions=[group1, cond2]
        )
        
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(root) is True

    def test_keywords_match(self, candidate_info, resume_text):
        # Keywords CONTAINS "microservices"
        condition = FilterCondition(
            field="keywords",
            operator=ComparisonOperator.CONTAINS,
            value="microservices"
        )
        evaluator = ConditionEvaluator(candidate_info, text_content=resume_text)
        assert evaluator.evaluate(condition) is True

    def test_education_level_comparison(self, candidate_info):
        # Master >= Bachelor -> True
        condition = FilterCondition(
            field="education_level",
            operator=ComparisonOperator.GTE,
            value="bachelor"
        )
        evaluator = ConditionEvaluator(candidate_info)
        assert evaluator.evaluate(condition) is True

        # Master >= Doctor -> False
        condition2 = FilterCondition(
            field="education_level",
            operator=ComparisonOperator.GTE,
            value="doctor"
        )
        assert evaluator.evaluate(condition2) is False
