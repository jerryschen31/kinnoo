from pathlib import Path
import importlib.util
import sys

import pytest

from kinnoo.registry import RegistryBackend, RegistryService
from kinnoo.registry_backends import LocalFilesystemRegistryBackend


# [agent] test deprecated: Feature12 registry tests are superseded by feature13 tests.
# def test_registry_backend_contract_and_local_layout(tmp_path: Path) -> None:
#     ...
#
# def test_registry_version_resolution_latest_and_exact(tmp_path: Path) -> None:
#     ...


def _load_feature26_filesystem_fixture_module():
	"""Load the feature26 filesystem MCP fixture run module by file path."""
	fixture_path = (
		Path(__file__).resolve().parents[1]
		/ "scratch"
		/ "feature26-filesystem-mcp-server"
		/ "run.py"
	)
	spec = importlib.util.spec_from_file_location("feature26_filesystem_fixture", fixture_path)
	assert spec is not None and spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = module
	spec.loader.exec_module(module)
	return module


def test_feature26_filesystem_permissions_runtime_enforcement(tmp_path: Path) -> None:
	"""Feature26 test238: permission checks hold at helper and MCP tools/call handler levels."""
	fixture = _load_feature26_filesystem_fixture_module()

	default_permissions = fixture.permissions_from_manifest({})
	default_gate = fixture.FilesystemPermissionGate(default_permissions, tmp_path)

	blocked_target = tmp_path / "notes.txt"
	with pytest.raises(fixture.FilesystemPermissionError) as write_error:
		default_gate.assert_allowed("write", blocked_target)
	assert "read-only mode" in str(write_error.value)

	with pytest.raises(fixture.FilesystemPermissionError) as create_error:
		default_gate.assert_allowed("create", blocked_target)
	assert "read-only mode" in str(create_error.value)

	blocked_request = {
		"jsonrpc": "2.0",
		"id": 1,
		"method": "tools/call",
		"params": {
			"name": "filesystem.write",
			"arguments": {"path": str(blocked_target)},
		},
	}
	with pytest.raises(fixture.FilesystemPermissionError) as handler_write_error:
		fixture.handle_mcp_tool_call(blocked_request, default_gate)
	assert "read-only mode" in str(handler_write_error.value)

	allowed_root = tmp_path / "allowed"
	allowed_root.mkdir(parents=True, exist_ok=True)
	allowed_permissions = fixture.permissions_from_manifest(
		{
			"permissions": {
				"read_only": False,
				"allow_write": True,
				"allow_create": True,
				"allowed_paths": ["allowed"],
			}
		}
	)
	allow_gate = fixture.FilesystemPermissionGate(allowed_permissions, tmp_path)

	allowed_target = allowed_root / "doc.txt"
	resolved_target = allow_gate.assert_allowed("write", allowed_target)
	assert resolved_target == allowed_target.resolve()

	created_target = allow_gate.assert_allowed("create", allowed_target)
	assert created_target == allowed_target.resolve()

	allowed_request = {
		"jsonrpc": "2.0",
		"id": 2,
		"method": "tools/call",
		"params": {
			"name": "filesystem.create",
			"arguments": {"path": str(allowed_target)},
		},
	}
	response = fixture.handle_mcp_tool_call(allowed_request, allow_gate)
	assert response["ok"] is True
	assert response["action"] == "create"
	assert response["resolved_path"] == str(allowed_target.resolve())

	outside_target = tmp_path / "outside.txt"
	with pytest.raises(fixture.FilesystemPermissionError) as sandbox_error:
		allow_gate.assert_allowed("write", outside_target)
	assert "allowed_paths sandbox" in str(sandbox_error.value)

	outside_request = {
		"jsonrpc": "2.0",
		"id": 3,
		"method": "tools/call",
		"params": {
			"name": "filesystem.write",
			"arguments": {"path": str(outside_target)},
		},
	}
	with pytest.raises(fixture.FilesystemPermissionError) as handler_sandbox_error:
		fixture.handle_mcp_tool_call(outside_request, allow_gate)
	assert "allowed_paths sandbox" in str(handler_sandbox_error.value)
