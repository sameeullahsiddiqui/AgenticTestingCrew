import os
import shutil
import pytest

from scripts.clean_logs import clean


@pytest.fixture(autouse=True)
def setup_and_teardown(tmp_path, monkeypatch):
    # Create dummy logs and screenshots directories
    logs_dir = tmp_path / "logs"
    screenshots_dir = tmp_path / "screenshots"
    logs_dir.mkdir()
    screenshots_dir.mkdir()

    # Create dummy files
    (logs_dir / "old.log").write_text("dummy log")
    (screenshots_dir / "img.png").write_bytes(b"\x89PNG...dummy")

    # Monkeypatch paths in clean_logs script
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLEAN_LOGS_PATHS", f"{logs_dir},{screenshots_dir}")
    yield

    # Cleanup
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    if screenshots_dir.exists():
        shutil.rmtree(screenshots_dir)


def test_clean_removes_all_files(tmp_path, monkeypatch, capsys):
    # Execute clean
    clean()
    # After clean, directories should be empty
    logs_dir = tmp_path / "logs"
    screenshots_dir = tmp_path / "screenshots"
    assert not any(logs_dir.iterdir()), "Logs directory should be empty"
    assert not any(screenshots_dir.iterdir()), "Screenshots directory should be empty"

    # Check console output
    captured = capsys.readouterr()
    assert "✅ Logs and screenshots cleaned." in captured.out


# File: backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_list_files_empty(tmp_path, monkeypatch):
    # Monkeypatch fs_files directory
    monkeypatch.setenv("FS_PATH", str(tmp_path))
    response = client.get("/list-files")
    assert response.status_code == 200
    assert response.json() == []


def test_download_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setenv("FS_PATH", str(tmp_path))
    response = client.get("/download/nonexistent.txt")
    assert response.status_code == 404


# File: backend/tests/__init__.py
# (empty to mark tests package)
