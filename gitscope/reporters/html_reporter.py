from __future__ import annotations

from importlib import resources
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from gitscope.core.models.report import ReportPayload


class HtmlReporter:
    def write(self, output_path: Path, payload: ReportPayload) -> Path:
        template_dir = resources.files("gitscope.templates")
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("report.html.j2")

        self._copy_asset("style.css", output_path / "assets" / "style.css")
        self._copy_asset("app.js", output_path / "assets" / "app.js")

        html = template.render(report=payload.model_dump(mode="json"))
        target = output_path / "index.html"
        target.write_text(html, encoding="utf-8")
        return target

    def _copy_asset(self, asset_name: str, destination: Path) -> None:
        asset = resources.files("gitscope.assets").joinpath(asset_name)
        destination.write_text(asset.read_text(encoding="utf-8"), encoding="utf-8")
