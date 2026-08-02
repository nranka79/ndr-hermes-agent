"""Regression test: tool modules that self-register must be auto-discovered.

``tools/smart_browser_tool.py`` and ``tools/browser_use_cloud_tool.py`` were
silently skipped by ``discover_builtin_tools()`` because they wrapped
``registry.register()`` inside a helper function; the AST scan in
``tools/registry.py::_module_registers_tools`` only detects top-level
``registry.register(...)`` call expressions.

These tests fail (red) on the pre-fix code and pass (green) on the fix.
"""

from pathlib import Path

from tools.registry import _module_registers_tools, registry


def _tool_path(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "tools" / name


def test_smart_browser_module_has_top_level_registration():
    assert _module_registers_tools(_tool_path("smart_browser_tool.py"))


def test_browser_use_cloud_module_has_top_level_registration():
    assert _module_registers_tools(_tool_path("browser_use_cloud_tool.py"))


def test_importing_modules_registers_tools():
    import tools.browser_use_cloud_tool  # noqa: F401
    import tools.smart_browser_tool  # noqa: F401

    names = set(registry.get_all_tool_names())
    assert "smart_browser" in names
    assert "browser_use_cloud" in names
