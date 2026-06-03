from types import SimpleNamespace

from orchestration import cli


def test_run_pipeline_uses_default_config_by_convention(monkeypatch):
    calls = []

    def fake_runner(
        pipeline_config_path: str,
        platform_config_path: str,
        source_name: str | None,
    ) -> list[dict[str, str | int]]:
        calls.append((pipeline_config_path, platform_config_path, source_name))
        return []

    monkeypatch.setattr(cli, "load_pipeline_runner", lambda pipeline_name: fake_runner)

    cli.run_pipeline(
        SimpleNamespace(
            pipeline_name="company_registry",
            pipeline_config=None,
            platform_config="configs/platforms/local.yml",
            source=None,
        )
    )

    assert calls == [
        (
            "configs/pipelines/company_registry.yml",
            "configs/platforms/local.yml",
            None,
        )
    ]


def test_run_pipeline_passes_source_filter(monkeypatch):
    calls = []

    def fake_runner(
        pipeline_config_path: str,
        platform_config_path: str,
        source_name: str | None,
    ) -> list[dict[str, str | int]]:
        calls.append((pipeline_config_path, platform_config_path, source_name))
        return []

    monkeypatch.setattr(cli, "load_pipeline_runner", lambda pipeline_name: fake_runner)

    cli.run_pipeline(
        SimpleNamespace(
            pipeline_name="company_registry",
            pipeline_config=None,
            platform_config="configs/platforms/local.yml",
            source="simples",
        )
    )

    assert calls == [
        (
            "configs/pipelines/company_registry.yml",
            "configs/platforms/local.yml",
            "simples",
        )
    ]
