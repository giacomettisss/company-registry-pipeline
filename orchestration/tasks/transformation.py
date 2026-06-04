from pathlib import Path
import shutil
import subprocess
import sys

from prefect import get_run_logger, task

from orchestration.core.config import TransformationConfig


SUPPORTED_DBT_COMMANDS = {"run", "snapshot", "test"}


@task
def run_dbt_command(
    transformation_config: TransformationConfig,
    command: str,
) -> dict[str, str | int]:
    """Run one dbt command from the configured platform transformation settings.

    The task keeps dbt orchestration reusable across pipelines while preserving
    dbt as the owner of transformations, tests, snapshots, logs, and artifacts.
    """

    if transformation_config.type != "dbt":
        raise ValueError(f"Unsupported transformation type: {transformation_config.type}")

    if command not in SUPPORTED_DBT_COMMANDS:
        raise ValueError(f"Unsupported dbt command: {command}")

    logger = get_run_logger()
    project_root = transformation_config.project_dir.parent
    dbt_executable = _resolve_dbt_executable()
    dbt_command = [
        dbt_executable,
        command,
        "--project-dir",
        str(transformation_config.project_dir),
        "--profiles-dir",
        str(transformation_config.profiles_dir),
        "--target",
        transformation_config.target,
    ]

    logger.info(
        "Starting dbt command: command=%s project_dir=%s profiles_dir=%s target=%s",
        command,
        transformation_config.project_dir,
        transformation_config.profiles_dir,
        transformation_config.target,
    )

    completed_process = subprocess.run(
        dbt_command,
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed_process.stdout:
        logger.info("dbt %s stdout:\n%s", command, completed_process.stdout)

    if completed_process.stderr:
        logger.warning("dbt %s stderr:\n%s", command, completed_process.stderr)

    if completed_process.returncode != 0:
        raise RuntimeError(f"dbt {command} failed with exit code {completed_process.returncode}.")

    logger.info("dbt command completed: command=%s exit_code=%s", command, completed_process.returncode)

    return {
        "command": command,
        "target": transformation_config.target,
        "exit_code": completed_process.returncode,
    }


def _resolve_dbt_executable() -> str:
    """Return the dbt executable from the active environment or system PATH.

    The dbt package does not expose `python -m dbt` in this environment, so the
    task resolves the console executable installed with the virtual environment.
    """

    scripts_dir = Path(sys.executable).parent
    for executable_name in ("dbt.exe", "dbt.cmd", "dbt"):
        candidate = scripts_dir / executable_name
        if candidate.exists():
            return str(candidate)

    executable = shutil.which("dbt")
    if executable:
        return executable

    raise FileNotFoundError("dbt executable was not found in the active environment or PATH.")
