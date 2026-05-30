from __future__ import annotations

from pathlib import Path

import typer

from gitscope import __version__
from gitscope.core.services.analysis import AnalysisRequest, AnalysisService
from gitscope.core.utils.dates import parse_optional_date
from gitscope.core.utils.errors import GitScopeError

app = typer.Typer(no_args_is_help=True, help="Analyze a local Git repository and generate a report.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"GitScope {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: bool | None = typer.Option(
        None,
        "--version",
        help="Show the GitScope version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Configure the CLI."""


@app.command()
def analyze(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False, resolve_path=True),
    output: Path = typer.Option(
        Path("report"),
        "--output",
        "-o",
        help="Directory where report.json, index.html, and assets will be written.",
        resolve_path=True,
    ),
    branch: str | None = typer.Option(None, "--branch", help="Limit commit-based analysis to a single branch."),
    since: str | None = typer.Option(None, "--since", help="Inclusive start date in YYYY-MM-DD format."),
    until: str | None = typer.Option(None, "--until", help="Inclusive end date in YYYY-MM-DD format."),
) -> None:
    """Analyze a Git repository and write an HTML + JSON report."""
    request = AnalysisRequest(
        repo_path=repo_path,
        output_path=output,
        branch=branch,
        since=parse_optional_date(since),
        until=parse_optional_date(until),
    )

    try:
        result = AnalysisService().run(request)
    except GitScopeError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Report generated: {result.output_path}", fg=typer.colors.GREEN)


def main() -> None:
    app()
