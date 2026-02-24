import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Mock MinIO Client BEFORE import to avoid connection error
mock_minio_module = MagicMock()
sys.modules["src.storage.minio_client"] = mock_minio_module
mock_minio_module.minio_client = MagicMock() # The global instance

# Now import
try:
    from src.workflows.resume_workflow import _load_and_merge_conditions
except ImportError:
    # If import fails due to other deps, we might need to mock more
    # But usually MinIO is the only one connecting on init
    pass

import pytest

@pytest.mark.asyncio
async def test_load_and_merge_conditions_fix():
    # Mock data with integer IDs (simulating what comes from JSON)
    filter_config = {
        "groups": [{
            "logic": "or",
            "condition_ids": [1, 2] 
        }],
        "group_logic": "and",
        "exclude_condition_ids": [3]
    }
    
    # Mock DB result
    mock_cond1 = MagicMock()
    mock_cond1.id = 1
    mock_cond1.conditions = {"keywords": ["Java"]}
    
    mock_cond2 = MagicMock()
    mock_cond2.id = 2
    mock_cond2.conditions = {"keywords": ["Python"]}
    
    mock_cond3 = MagicMock()
    mock_cond3.id = 3
    mock_cond3.conditions = {"keywords": ["C++"]}
    
    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # The code calls scalars().all()
    mock_result.scalars.return_value.all.return_value = [mock_cond1, mock_cond2, mock_cond3]
    mock_session.execute.return_value = mock_result
    
    # Mock factory
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None
    
    # Patch
    # We need to patch where it is imported. Since it is imported from src.models inside the function
    # we patch src.models.async_session_factory
    with patch("src.models.async_session_factory", mock_factory):
        result = await _load_and_merge_conditions(filter_config)
        
    # Verify
    assert result is not None
    assert "filter_rules" in result
    root_group = result["filter_rules"]
    assert str(root_group.operator) == "and"
    
    # Check groups (OR group)
    assert len(root_group.conditions) == 2
    
    # First condition should be the OR group
    or_group = root_group.conditions[0]
    assert str(or_group.operator) == "or"
    assert len(or_group.conditions) == 2
    
    vals = set()
    for c in or_group.conditions:
        if hasattr(c, "value"):
            vals.add(c.value)
    
    assert "Java" in vals
    assert "Python" in vals
    
    # Second condition should be the Exclude group (NOT)
    not_group = root_group.conditions[1]
    assert str(not_group.operator) == "not"
    assert len(not_group.conditions) == 1
    assert not_group.conditions[0].value == "C++"
    
    print("Test Passed Successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_load_and_merge_conditions_fix())
