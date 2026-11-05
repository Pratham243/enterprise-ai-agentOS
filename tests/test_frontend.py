"""Tests verifying frontend component files exist and have expected content."""

import os

import pytest

FRONTEND_SRC = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "src"
)


def _read(path: str) -> str:
    full = os.path.join(FRONTEND_SRC, path)
    assert os.path.exists(full), f"Missing frontend file: {path}"
    with open(full) as f:
        return f.read()


def test_toast_component_exists():
    content = _read("components/Toast.jsx")
    assert "toast" in content.lower()
    assert "onClose" in content


def test_spinner_component_exists():
    content = _read("components/Spinner.jsx")
    assert "spinner" in content.lower()
    assert "Loading" in content


def test_theme_toggle_exists():
    content = _read("components/ThemeToggle.jsx")
    assert "data-theme" in content
    assert "localStorage" in content


def test_layout_includes_theme_toggle():
    content = _read("components/Layout.jsx")
    assert "ThemeToggle" in content


def test_css_has_light_theme():
    content = _read("index.css")
    assert '[data-theme="light"]' in content
    assert '[data-theme="dark"]' in content


def test_css_has_toast_styles():
    content = _read("index.css")
    assert ".toast" in content
    assert ".toast-error" in content
    assert ".toast-success" in content


def test_css_has_spinner_styles():
    content = _read("index.css")
    assert ".spinner" in content
    assert "@keyframes spin" in content


def test_askagent_uses_spinner_and_toast():
    content = _read("pages/AskAgent.jsx")
    assert "Spinner" in content
    assert "Toast" in content


def test_dashboard_uses_spinner_and_toast():
    content = _read("pages/Dashboard.jsx")
    assert "Spinner" in content
    assert "Toast" in content
