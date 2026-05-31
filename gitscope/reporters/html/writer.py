"""Render the static HTML report shell and copy local assets."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from gitscope.core.models.report import ReportDocument


class HTMLReportWriter:
    """Write index.html and local assets."""

    def __init__(self) -> None:
        package_root = Path(__file__).resolve().parents[2]
        self.template_dir = package_root / "templates"
        self.asset_dir = package_root / "assets"
        self.environment = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        )

    def write(self, output_dir: Path, report: ReportDocument) -> Path:
        assets_output = output_dir / "assets"
        assets_output.mkdir(parents=True, exist_ok=True)
        for asset_name in ("report.css", "report.js"):
            shutil.copyfile(self.asset_dir / asset_name, assets_output / asset_name)

        template = self.environment.get_template("report.html.j2")
        rendered = template.render(report_json=json.dumps(report.model_dump(mode="json"), ensure_ascii=False))
        index_path = output_dir / "index.html"
        index_path.write_text(rendered, encoding="utf-8")
        return index_path
