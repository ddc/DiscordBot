import pytest
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = "docker-compose.yml"
IMAGE_NAME = "discordbot-docker-test"


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def compose_file():
    return COMPOSE_FILE


@pytest.fixture(scope="session")
def image_name():
    return IMAGE_NAME


@pytest.fixture(scope="session")
def docker_build(project_root, image_name):
    """Build the python-base stage once per session."""
    result = subprocess.run(
        ["docker", "build", "--target", "python-base", "-t", image_name, "."],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Docker build failed:\n{result.stderr}"
    yield image_name
    subprocess.run(["docker", "rmi", "-f", image_name], capture_output=True)


def pytest_collection_modifyitems(config, items):
    if not shutil.which("docker"):
        skip_docker = pytest.mark.skip(reason="docker not available")
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_docker)
