from types import SimpleNamespace

from orchestration import cli


def test_run_pipeline_uses_default_config_by_convention(monkeypatch):
    calls = []

    def fake_runner(pipeline_config_path: str, platform_config_path: str) -> list[dict[str, str | int]]:
        calls.append((pipeline_config_path, platform_config_path))
        return []

    monkeypatch.setattr(cli, "load_pipeline_runner", lambda pipeline_name: fake_runner)

    cli.run_pipeline(
        SimpleNamespace(
            pipeline_name="company_registry",
            pipeline_config=None,
            platform_config="configs/platforms/local.yml",
        )
    )

    assert calls == [
        (
            "configs/pipelines/company_registry.yml",
            "configs/platforms/local.yml",
        )
    ]
