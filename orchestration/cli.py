from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from importlib import import_module
import re


DEFAULT_PLATFORM_CONFIG_PATH = "configs/platforms/local.yml"
DEFAULT_PIPELINE_CONFIG_TEMPLATE = "configs/pipelines/{pipeline_name}.yml"
PIPELINE_FLOW_MODULE_TEMPLATE = "pipelines.{pipeline_name}.flow"
PIPELINE_RUNNER_FUNCTION = "run_flow"
VALID_PIPELINE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")

PipelineRunResult = dict[str, list[dict[str, str | int]]]
PipelineRunner = Callable[[str, str, str | None], PipelineRunResult]


def parse_args() -> Namespace:
    """Parse the shared local CLI arguments for pipeline execution.

    The CLI is intentionally generic so users can run pipelines by name without
    memorizing Python module paths.
    """

    parser = ArgumentParser(description="Run local data pipeline flows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a pipeline flow.")
    run_parser.add_argument("pipeline_name", help="Pipeline folder name, for example: company_registry.")
    run_parser.add_argument(
        "--pipeline-config",
        help="Path to the pipeline YAML configuration. Defaults to configs/pipelines/<pipeline_name>.yml.",
    )
    run_parser.add_argument(
        "--platform-config",
        default=DEFAULT_PLATFORM_CONFIG_PATH,
        help="Path to the shared platform YAML configuration.",
    )
    run_parser.add_argument(
        "--source",
        help="Optional source name to run from the pipeline YAML. Defaults to all sources.",
    )

    return parser.parse_args()


def run_pipeline(args: Namespace) -> None:
    """Resolve and execute a pipeline flow from CLI arguments.

    Pipeline-specific behavior is loaded by convention, keeping the shared CLI
    stable as new domains are added.
    """

    if args.source:
        validate_source_name(args.source)

    runner = load_pipeline_runner(args.pipeline_name)
    pipeline_config_path = args.pipeline_config or DEFAULT_PIPELINE_CONFIG_TEMPLATE.format(
        pipeline_name=args.pipeline_name
    )

    runner(
        pipeline_config_path=pipeline_config_path,
        platform_config_path=args.platform_config,
        source_name=args.source,
    )


def load_pipeline_runner(pipeline_name: str) -> PipelineRunner:
    """Load a pipeline run function using the shared naming convention.

    A valid pipeline must expose `run_flow` from `pipelines.<name>.flow`, which
    avoids central registries that would need edits for every new pipeline.
    """

    validate_pipeline_name(pipeline_name)
    module_name = PIPELINE_FLOW_MODULE_TEMPLATE.format(pipeline_name=pipeline_name)
    module = import_module(module_name)
    runner = getattr(module, PIPELINE_RUNNER_FUNCTION, None)

    if not callable(runner):
        raise AttributeError(
            f"Pipeline module {module_name} must expose a callable {PIPELINE_RUNNER_FUNCTION}."
        )

    return runner


def validate_pipeline_name(pipeline_name: str) -> None:
    """Validate pipeline names before importing modules dynamically.

    The restriction keeps convention-based imports predictable and avoids
    accepting arbitrary module paths from the command line.
    """

    if not VALID_PIPELINE_NAME.match(pipeline_name):
        raise ValueError(
            "Invalid pipeline name. Use lowercase letters, numbers, and underscores only, "
            "starting with a letter."
        )


def validate_source_name(source_name: str) -> None:
    """Validate source names before selecting YAML source declarations.

    Source names use the same convention as pipeline names so CLI filters stay
    simple and safe.
    """

    if not VALID_PIPELINE_NAME.match(source_name):
        raise ValueError(
            "Invalid source name. Use lowercase letters, numbers, and underscores only, "
            "starting with a letter."
        )


def main() -> None:
    """CLI entrypoint used by `python -m orchestration.cli`."""

    args = parse_args()

    if args.command == "run":
        run_pipeline(args)
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
