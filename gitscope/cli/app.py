"""Typer-based CLI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from gitscope import __version__
from gitscope.core.git.errors import GitScopeError
from gitscope.core.models.domain import AnalysisRequest
from gitscope.core.services.analysis_service import AnalysisService

app = typer.Typer(add_completion=False, help="Analyze local Git repositories and generate static reports.")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"GitScope {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the GitScope version and exit.",
        ),
    ] = False,
) -> None:
    del version


@app.command()
def analyze(
    repo_path: Annotated[Path, typer.Argument(help="Path to the local Git repository.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory where the report will be written."),
    ] = Path("report"),
    branch: Annotated[
        str | None,
        typer.Option("--branch", help="Optional branch to scope commit analysis to."),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option("--since", help="Optional ISO date or datetime lower bound."),
    ] = None,
    until: Annotated[
        str | None,
        typer.Option("--until", help="Optional ISO date or datetime upper bound."),
    ] = None,
) -> None:
    """Collect Git data, analyze it locally, and generate a static report."""

    try:
        service = AnalysisService()
        result = service.analyze(
            AnalysisRequest(
                repo_path=repo_path,
                output_path=output,
                branch=branch,
                since=since,
                until=until,
            )
        )
    except GitScopeError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Generated report at {result.index_path}")


if __name__ == "__main__":
    app()
