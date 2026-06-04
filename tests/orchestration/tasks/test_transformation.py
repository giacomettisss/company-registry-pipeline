from types import SimpleNamespace

from orchestration.core.config import TransformationConfig
from orchestration.tasks import transformation


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


def test_run_dbt_command_uses_platform_transformation_config(monkeypatch, tmp_path):
    calls = {}

    def fake_run(command, cwd, capture_output, text, encoding, errors, check):
        calls["command"] = command
        calls["cwd"] = cwd
        calls["capture_output"] = capture_output
        calls["text"] = text
        calls["encoding"] = encoding
        calls["errors"] = errors
        calls["check"] = check
        return SimpleNamespace(stdout="dbt ok", stderr="", returncode=0)

    monkeypatch.setattr(transformation, "get_run_logger", lambda: FakeLogger())
    monkeypatch.setattr(transformation, "_resolve_dbt_executable", lambda: "dbt")
    monkeypatch.setattr(transformation.subprocess, "run", fake_run)

    config = TransformationConfig(
        type="dbt",
        target="local",
        project_dir=tmp_path / "dbt_data_platform",
        profiles_dir=tmp_path / "dbt_data_platform",
    )

    result = transformation.run_dbt_command.fn(config, "run")

    assert result == {"command": "run", "target": "local", "exit_code": 0}
    assert calls["command"] == [
        "dbt",
        "run",
        "--project-dir",
        str(config.project_dir),
        "--profiles-dir",
        str(config.profiles_dir),
        "--target",
        "local",
    ]
    assert calls["cwd"] == tmp_path
    assert calls["capture_output"] is True
    assert calls["text"] is True
    assert calls["encoding"] == "utf-8"
    assert calls["errors"] == "replace"
    assert calls["check"] is False
