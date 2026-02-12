import pytest
import shutil
import subprocess

pytestmark = pytest.mark.docker


class TestDockerLint:
    def test_hadolint_dockerfile(self, project_root):
        """Dockerfile passes hadolint linting."""
        dockerfile = project_root / "Dockerfile"
        hadolint_config = project_root / ".hadolint.yaml"
        cmd = ["docker", "run", "--rm", "-i"]
        if hadolint_config.exists():
            cmd += ["-v", f"{hadolint_config}:/.config/hadolint.yaml:ro"]
        cmd.append("hadolint/hadolint")
        result = subprocess.run(
            cmd,
            input=dockerfile.read_text(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"Hadolint errors:\n{result.stdout}"


class TestComposeConfig:
    def test_compose_config(self, project_root, compose_file):
        """Compose file parses correctly with env vars."""
        env_example = project_root / ".env.example"
        env_file = project_root / ".env"
        cleanup = False
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            cleanup = True
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", compose_file, "config", "--quiet"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"Compose config failed:\n{result.stderr}"
        finally:
            if cleanup:
                env_file.unlink(missing_ok=True)


class TestDockerfileStructure:
    def test_multistage_build(self, project_root):
        """Dockerfile has both python-base and final stages."""
        content = (project_root / "Dockerfile").read_text()
        assert "AS python-base" in content, "Missing python-base stage"
        assert "FROM python-base AS final" in content, "Missing final stage"


class TestDockerBuild:
    def test_docker_build_base(self, docker_build):
        """docker build --target python-base succeeds."""
        assert docker_build is not None


class TestDockerSmoke:
    def test_python_available(self, docker_build):
        """Python is available and is 3.14.x in the base image."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_build, "python", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"python --version failed:\n{result.stderr}"
        assert "3.14" in result.stdout, f"Expected Python 3.14, got: {result.stdout}"

    def test_uv_available(self, docker_build):
        """uv is available in the base image."""
        result = subprocess.run(
            ["docker", "run", "--rm", docker_build, "uv", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"uv --version failed:\n{result.stderr}"
        assert "uv" in result.stdout, f"Unexpected uv output: {result.stdout}"
