import pytest
from unittest.mock import patch, AsyncMock

from data_discovery.core.service import DataDiscoveryService

@pytest.fixture
def service():
    return DataDiscoveryService()

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_no_filter_returns_all(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1", "proj2"]
    mock_pm.get_project_by_id.side_effect = [
        {"id": "proj1", "blockchain": "eth", "description": "desc1", "aliases": []},
        {"id": "proj2", "blockchain": "btc", "description": "desc2", "aliases": []},
    ]
    result = await service.get_resources()
    assert result["success"] is True
    assert len(result["data"]) == 2

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_with_blockchain_filter(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1", "proj2"]
    mock_pm.get_project_by_id.side_effect = [
        {"id": "proj1", "blockchain": "eth", "description": "desc1", "aliases": []},
        {"id": "proj2", "blockchain": "btc", "description": "desc2", "aliases": []},
    ]
    result = await service.get_resources(blockchain_filter="eth")
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["blockchain"] == "eth"

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_with_category_filter(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1", "proj2"]
    mock_pm.get_project_by_id.side_effect = [
        {"id": "proj1", "blockchain": "eth", "category": "L1", "description": "desc1", "aliases": []},
        {"id": "proj2", "blockchain": "btc", "category": "L2", "description": "desc2", "aliases": []},
    ]
    result = await service.get_resources(category_filter="L1", show_details=True)
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["category"] == "L1"

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_show_details_true(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1"]
    mock_pm.get_project_by_id.return_value = {
        "id": "proj1", "blockchain": "eth", "category": "L1", "description": "desc1", "aliases": [], "extra": "foo"
    }
    result = await service.get_resources(show_details=True)
    assert result["success"] is True
    assert "extra" in result["data"][0]
    assert result["data"][0]["category"] == "L1"

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_both_filters(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1", "proj2", "proj3"]
    mock_pm.get_project_by_id.side_effect = [
        {"id": "proj1", "blockchain": "eth", "category": "L1", "description": "desc1", "aliases": []},
        {"id": "proj2", "blockchain": "eth", "category": "L2", "description": "desc2", "aliases": []},
        {"id": "proj3", "blockchain": "btc", "category": "L1", "description": "desc3", "aliases": []},
    ]
    result = await service.get_resources(blockchain_filter="eth", category_filter="L1", show_details=True)
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "proj1"

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_empty(mock_pm, service):
    mock_pm.list_project_ids.return_value = []
    result = await service.get_resources()
    assert result["success"] is False
    assert result["data"] == []

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_resources_error_handling(mock_pm, service):
    mock_pm.list_project_ids.side_effect = Exception("fail")
    result = await service.get_resources()
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_models_invalid_level(mock_pm, service):
    result = await service.get_models(level="platinum")
    assert result["success"] is False
    assert "Invalid level" in result["error"]

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_models_with_schema_filter(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1"]
    mock_pm.get_project_artifacts = AsyncMock(return_value={
        "proj1": ({"nodes": {"model.proj1.table1": {"resource_type": "model", "schema": "core", "name": "table1", "resource_id": "proj1"}}}, {})
    })
    result = await service.get_models(schema="core")
    assert result["success"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["schema"] == "core"

@pytest.mark.asyncio
@patch("data_discovery.core.service.project_manager")
async def test_get_models_with_limit(mock_pm, service):
    mock_pm.list_project_ids.return_value = ["proj1"]
    mock_pm.get_project_artifacts = AsyncMock(return_value={
        "proj1": ({"nodes": {f"model.proj1.table{i}": {"resource_type": "model", "schema": "core", "name": f"table{i}", "resource_id": "proj1"} for i in range(10)}}, {})
    })
    result = await service.get_models(schema="core", limit=5)
    assert result["success"] is True
    assert len(result["data"]) == 5 