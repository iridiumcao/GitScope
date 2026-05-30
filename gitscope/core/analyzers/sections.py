from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from gitscope.core.models.report import ChartSeries, ChartSpec, HeatmapCell, ReportPayload, ReportSection, SummaryCard, TableSpec
from gitscope.core.utils.dates import (
    format_datetime,
    iso_week_key,
    month_key,
    safe_day_span,
    short_date,
)
from gitscope.storage.schema import BranchRecord, CommitFileRecord, CommitRecord, ContributorRecord, FileRecord, RepositoryRecord, TagRecord

PAGE_ORDER = ["overview", "commits", "contributors", "branches", "files", "timeline"]


def build_report_payload(
    session: Session,
    filters: dict[str, str | None],
) -> ReportPayload:
    repository = session.scalars(select(RepositoryRecord)).one()
    commits = list(session.scalars(select(CommitRecord).order_by(CommitRecord.committed_at)).all())
    contributors = list(session.scalars(select(ContributorRecord).order_by(ContributorRecord.name)).all())
    branches = list(session.scalars(select(BranchRecord).order_by(BranchRecord.name)).all())
    files = list(session.scalars(select(FileRecord).order_by(FileRecord.path)).all())
    commit_files = list(session.scalars(select(CommitFileRecord)).all())
    tags = list(session.scalars(select(TagRecord).order_by(TagRecord.name)).all())

    pages = {
        "overview": _build_overview(repository, commits, contributors, branches, files, commit_files, tags),
        "commits": _build_commits(commits),
        "contributors": _build_contributors(commits, contributors, commit_files, files),
        "branches": _build_branches(branches),
        "files": _build_files(files, commit_files),
        "timeline": _build_timeline(commits),
    }

    return ReportPayload(
        metadata={
            "repository_name": repository.name,
            "repository_path": repository.path,
            "current_branch": repository.current_branch,
            "default_branch": repository.default_branch,
            "since": filters["since"],
            "until": filters["until"],
            "branch": filters["branch"],
            "generated_at": format_datetime(datetime.now(UTC)),
        },
        page_order=PAGE_ORDER,
        pages=pages,
    )


def _build_overview(
    repository: RepositoryRecord,
    commits: list[CommitRecord],
    contributors: list[ContributorRecord],
    branches: list[BranchRecord],
    files: list[FileRecord],
    commit_files: list[CommitFileRecord],
    tags: list[TagRecord],
) -> ReportSection:
    monthly_commit_counts = _counts_by(commits, lambda item: month_key(item.committed_at))
    contributor_growth = _contributor_growth(commits)
    contributor_totals = _contributor_totals(commits, commit_files, files)
    file_totals = _file_totals(commit_files, files)

    age_days = _age_days(repository.first_commit_at, repository.last_commit_at)
    cards = [
        SummaryCard(label="Repository Name", value=repository.name),
        SummaryCard(label="Repository Path", value=repository.path),
        SummaryCard(label="First Commit", value=short_date(repository.first_commit_at)),
        SummaryCard(label="Last Commit", value=short_date(repository.last_commit_at)),
        SummaryCard(label="Repository Age", value=f"{age_days} days"),
        SummaryCard(label="Current Branch", value=repository.current_branch),
        SummaryCard(label="Default Branch", value=repository.default_branch),
        SummaryCard(label="Total Commits", value=str(len(commits))),
        SummaryCard(label="Total Contributors", value=str(len(contributors))),
        SummaryCard(label="Total Branches", value=str(len(branches))),
        SummaryCard(label="Total Tags", value=str(len(tags))),
        SummaryCard(label="Total Files", value=str(len(files))),
    ]
    return ReportSection(
        summary={
            "total_commits": len(commits),
            "total_contributors": len(contributors),
            "total_branches": len(branches),
            "total_tags": len(tags),
            "total_files": len(files),
        },
        cards=cards,
        charts=[
            _single_series_chart(
                chart_type="line",
                title="Monthly Commit Trend",
                description="Commits grouped by month.",
                counts=monthly_commit_counts,
            ),
            _single_series_chart(
                chart_type="line",
                title="Monthly Contributor Growth",
                description="Cumulative distinct contributors by month.",
                counts=contributor_growth,
            ),
        ],
        tables=[
            TableSpec(
                title="Top Contributors",
                columns=["name", "commits", "additions", "deletions", "files_modified"],
                rows=contributor_totals[:10],
                empty_message="No contributors were found in the selected scope.",
            ),
            TableSpec(
                title="Most Changed Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=file_totals["most_changed"][:10],
                empty_message="No file changes were found in the selected scope.",
            ),
        ],
        empty_state="No commits matched the selected filters." if not commits else None,
    )


def _build_commits(commits: list[CommitRecord]) -> ReportSection:
    total_commits = len(commits)
    total_additions = sum(item.additions for item in commits)
    total_deletions = sum(item.deletions for item in commits)
    average_changed_files = round(mean(item.changed_files for item in commits), 2) if commits else 0.0
    span_days = safe_day_span(commits[0].committed_at if commits else None, commits[-1].committed_at if commits else None)

    largest = sorted(commits, key=lambda item: (item.additions + item.deletions, item.changed_files), reverse=True)[:10]
    smallest = sorted(commits, key=lambda item: (item.additions + item.deletions, item.changed_files, item.committed_at))[:10]

    return ReportSection(
        summary={
            "total_commits": total_commits,
            "average_per_day": round(total_commits / span_days, 2),
            "average_per_week": round(total_commits / max(span_days / 7, 1), 2),
            "average_per_month": round(total_commits / max(span_days / 30, 1), 2),
            "average_additions": round(total_additions / total_commits, 2) if commits else 0.0,
            "average_deletions": round(total_deletions / total_commits, 2) if commits else 0.0,
            "average_changed_files": average_changed_files,
        },
        cards=[
            SummaryCard(label="Total Commits", value=str(total_commits)),
            SummaryCard(label="Average Per Day", value=f"{round(total_commits / span_days, 2)}"),
            SummaryCard(label="Average Per Week", value=f"{round(total_commits / max(span_days / 7, 1), 2)}"),
            SummaryCard(label="Average Per Month", value=f"{round(total_commits / max(span_days / 30, 1), 2)}"),
            SummaryCard(label="Average Additions", value=f"{round(total_additions / total_commits, 2) if commits else 0.0}"),
            SummaryCard(label="Average Deletions", value=f"{round(total_deletions / total_commits, 2) if commits else 0.0}"),
            SummaryCard(label="Average Changed Files", value=str(average_changed_files)),
        ],
        charts=[
            _single_series_chart("line", "Commit Trend by Day", "Daily commit totals.", _counts_by(commits, lambda item: item.committed_at.date().isoformat())),
            _single_series_chart("line", "Commit Trend by Week", "Weekly commit totals.", _counts_by(commits, lambda item: iso_week_key(item.committed_at))),
            _single_series_chart("line", "Commit Trend by Month", "Monthly commit totals.", _counts_by(commits, lambda item: month_key(item.committed_at))),
            _single_series_chart("bar", "Commit Size Distribution", "Distribution by changed lines.", _commit_size_distribution(commits)),
        ],
        tables=[
            TableSpec(
                title="Largest Commits",
                columns=["sha", "date", "message", "size", "changed_files"],
                rows=[_commit_row(item) for item in largest],
                empty_message="No commits were found in the selected scope.",
            ),
            TableSpec(
                title="Smallest Commits",
                columns=["sha", "date", "message", "size", "changed_files"],
                rows=[_commit_row(item) for item in smallest],
                empty_message="No commits were found in the selected scope.",
            ),
        ],
        empty_state="No commits matched the selected filters." if not commits else None,
    )


def _build_contributors(
    commits: list[CommitRecord],
    contributors: list[ContributorRecord],
    commit_files: list[CommitFileRecord],
    files: list[FileRecord],
) -> ReportSection:
    contributor_totals = _contributor_totals(commits, commit_files, files)
    by_author = defaultdict(list)
    for commit in commits:
        by_author[commit.author_id].append(commit)

    hourly = Counter(commit.committed_at.hour for commit in commits)
    weekly = Counter(commit.committed_at.strftime("%A") for commit in commits)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return ReportSection(
        summary={"total_contributors": len(contributors)},
        cards=[
            SummaryCard(label="Total Contributors", value=str(len(contributors))),
            SummaryCard(label="Most Active Contributor", value=contributor_totals[0]["name"] if contributor_totals else "N/A"),
        ],
        charts=[
            ChartSpec(
                type="bar",
                title="Hourly Activity Distribution",
                description="Commits grouped by author hour.",
                labels=[f"{hour:02d}:00" for hour in range(24)],
                series=[ChartSeries(name="Commits", values=[hourly.get(hour, 0) for hour in range(24)])],
            ),
            ChartSpec(
                type="bar",
                title="Weekly Activity Distribution",
                description="Commits grouped by weekday.",
                labels=weekday_order,
                series=[ChartSeries(name="Commits", values=[weekly.get(day, 0) for day in weekday_order])],
            ),
            _single_series_chart(
                chart_type="bar",
                title="Commit Size Distribution",
                description="Distribution of commit sizes across all contributors.",
                counts=_commit_size_distribution(commits),
            ),
        ],
        tables=[
            TableSpec(
                title="Contributor Ranking",
                columns=["name", "email", "commits", "additions", "deletions", "files_modified"],
                rows=contributor_totals,
                empty_message="No contributors were found in the selected scope.",
            ),
            TableSpec(
                title="Contributor Details",
                columns=["name", "last_commit", "average_commit_size", "peak_hour"],
                rows=[
                    {
                        "name": contributor.name,
                        "last_commit": short_date(max((commit.committed_at for commit in by_author.get(contributor.id, [])), default=None)),
                        "average_commit_size": round(
                            mean((commit.additions + commit.deletions) for commit in by_author.get(contributor.id, [])),
                            2,
                        )
                        if by_author.get(contributor.id)
                        else 0,
                        "peak_hour": _peak_hour(by_author.get(contributor.id, [])),
                    }
                    for contributor in contributors
                ],
                empty_message="No contributor details are available.",
            ),
        ],
        empty_state="No contributors were found in the selected scope." if not contributors else None,
    )


def _build_branches(branches: list[BranchRecord]) -> ReportSection:
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(days=90)
    rows = []
    stale_count = 0
    local_count = 0
    remote_count = 0
    for branch in branches:
        local_count += int(branch.is_local)
        remote_count += int(branch.is_remote)
        statuses: list[str] = []
        if branch.last_commit_at and branch.last_commit_at.replace(tzinfo=UTC) < stale_cutoff:
            statuses.append("STALE")
            stale_count += 1
        else:
            statuses.append("ACTIVE")
        if branch.ahead_count:
            statuses.append("AHEAD")
        if branch.behind_count:
            statuses.append("BEHIND")
        rows.append(
            {
                "name": branch.name,
                "scope": "local" if branch.is_local else "remote",
                "last_commit": short_date(branch.last_commit_at),
                "ahead": branch.ahead_count,
                "behind": branch.behind_count,
                "status": ", ".join(statuses),
            }
        )

    return ReportSection(
        summary={
            "total_branches": len(branches),
            "local_branches": local_count,
            "remote_branches": remote_count,
            "stale_branches": stale_count,
        },
        cards=[
            SummaryCard(label="Total Branches", value=str(len(branches))),
            SummaryCard(label="Local Branches", value=str(local_count)),
            SummaryCard(label="Remote Branches", value=str(remote_count)),
            SummaryCard(label="Stale Branches", value=str(stale_count), hint="No commits for 90 days."),
        ],
        charts=[
            ChartSpec(
                type="bar",
                title="Ahead / Behind by Branch",
                description="Ahead and behind counts relative to the default comparison branch.",
                labels=[row["name"] for row in rows[:20]],
                series=[
                    ChartSeries(name="Ahead", values=[row["ahead"] for row in rows[:20]]),
                    ChartSeries(name="Behind", values=[row["behind"] for row in rows[:20]]),
                ],
            )
        ],
        tables=[
            TableSpec(
                title="Branch List",
                columns=["name", "scope", "last_commit", "ahead", "behind", "status"],
                rows=rows,
                empty_message="No branches were found in the repository.",
            ),
            TableSpec(
                title="Stale Branches",
                columns=["name", "scope", "last_commit", "ahead", "behind", "status"],
                rows=[row for row in rows if "STALE" in row["status"]],
                empty_message="No stale branches were detected.",
            ),
        ],
        empty_state="No branches were found in the repository." if not branches else None,
    )


def _build_files(files: list[FileRecord], commit_files: list[CommitFileRecord]) -> ReportSection:
    totals = _file_totals(commit_files, files)
    return ReportSection(
        summary={"total_files": len(files)},
        cards=[
            SummaryCard(label="Total Files", value=str(len(files))),
            SummaryCard(label="Most Changed File", value=totals["most_changed"][0]["path"] if totals["most_changed"] else "N/A"),
            SummaryCard(label="Most Added File", value=totals["most_added"][0]["path"] if totals["most_added"] else "N/A"),
            SummaryCard(label="Most Deleted File", value=totals["most_deleted"][0]["path"] if totals["most_deleted"] else "N/A"),
        ],
        tables=[
            TableSpec(
                title="Most Changed Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=totals["most_changed"][:20],
                empty_message="No changed files were found.",
            ),
            TableSpec(
                title="Most Added Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=totals["most_added"][:20],
                empty_message="No added files were found.",
            ),
            TableSpec(
                title="Most Deleted Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=totals["most_deleted"][:20],
                empty_message="No deleted files were found.",
            ),
            TableSpec(
                title="Recently Active Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=totals["recent"][:20],
                empty_message="No recently active files were found.",
            ),
            TableSpec(
                title="Inactive Files",
                columns=["path", "changes", "additions", "deletions", "last_seen"],
                rows=totals["inactive"][:20],
                empty_message="No inactive files were found.",
            ),
        ],
        empty_state="No file history was found in the selected scope." if not commit_files else None,
    )


def _build_timeline(commits: list[CommitRecord]) -> ReportSection:
    if commits:
        busiest_day = max(_counts_by(commits, lambda item: item.committed_at.date().isoformat()).items(), key=lambda item: item[1])
        busiest_week = max(_counts_by(commits, lambda item: iso_week_key(item.committed_at)).items(), key=lambda item: item[1])
        busiest_month = max(_counts_by(commits, lambda item: month_key(item.committed_at)).items(), key=lambda item: item[1])
    else:
        busiest_day = ("N/A", 0)
        busiest_week = ("N/A", 0)
        busiest_month = ("N/A", 0)

    return ReportSection(
        cards=[
            SummaryCard(label="Peak Day", value=busiest_day[0], hint=f"{busiest_day[1]} commits"),
            SummaryCard(label="Peak Week", value=busiest_week[0], hint=f"{busiest_week[1]} commits"),
            SummaryCard(label="Peak Month", value=busiest_month[0], hint=f"{busiest_month[1]} commits"),
        ],
        charts=[
            _single_series_chart("line", "Commit Timeline by Day", "Daily commit totals.", _counts_by(commits, lambda item: item.committed_at.date().isoformat())),
            _single_series_chart("line", "Commit Timeline by Week", "Weekly commit totals.", _counts_by(commits, lambda item: iso_week_key(item.committed_at))),
            _single_series_chart("line", "Commit Timeline by Month", "Monthly commit totals.", _counts_by(commits, lambda item: month_key(item.committed_at))),
            ChartSpec(
                type="heatmap",
                title="Commit Heatmap",
                description="Commit activity over the last 365 days.",
                cells=_heatmap_cells(commits),
            ),
        ],
        empty_state="No commits matched the selected filters." if not commits else None,
    )


def _counts_by(items: list[CommitRecord], key_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = key_fn(item)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _single_series_chart(chart_type: str, title: str, description: str, counts: dict[str, int]) -> ChartSpec:
    return ChartSpec(
        type=chart_type,
        title=title,
        description=description,
        labels=list(counts.keys()),
        series=[ChartSeries(name=title, values=list(counts.values()))],
    )


def _contributor_growth(commits: list[CommitRecord]) -> dict[str, int]:
    seen: set[int] = set()
    growth: dict[str, int] = {}
    for commit in sorted(commits, key=lambda item: item.committed_at):
        seen.add(commit.author_id)
        growth[month_key(commit.committed_at)] = len(seen)
    return dict(sorted(growth.items(), key=lambda item: item[0]))


def _contributor_totals(
    commits: list[CommitRecord],
    commit_files: list[CommitFileRecord],
    files: list[FileRecord],
) -> list[dict[str, object]]:
    file_lookup = {item.id: item.path for item in files}
    commit_to_files: dict[str, set[str]] = defaultdict(set)
    for commit_file in commit_files:
        path = file_lookup.get(commit_file.file_id)
        if path:
            commit_to_files[commit_file.commit_sha].add(path)

    rows: dict[int, dict[str, object]] = {}
    for commit in commits:
        entry = rows.setdefault(
            commit.author_id,
            {
                "name": commit.author_name,
                "email": commit.author_email,
                "commits": 0,
                "additions": 0,
                "deletions": 0,
                "files_modified": set(),
            },
        )
        entry["commits"] = int(entry["commits"]) + 1
        entry["additions"] = int(entry["additions"]) + commit.additions
        entry["deletions"] = int(entry["deletions"]) + commit.deletions
        entry["files_modified"].update(commit_to_files.get(commit.sha, set()))

    result = []
    for entry in rows.values():
        result.append(
            {
                "name": entry["name"],
                "email": entry["email"],
                "commits": entry["commits"],
                "additions": entry["additions"],
                "deletions": entry["deletions"],
                "files_modified": len(entry["files_modified"]),
            }
        )
    result.sort(key=lambda item: (-int(item["commits"]), str(item["name"]).lower()))
    return result


def _file_totals(commit_files: list[CommitFileRecord], files: list[FileRecord]) -> dict[str, list[dict[str, object]]]:
    file_lookup = {item.id: item for item in files}
    rows = []
    grouped: dict[int, dict[str, object]] = defaultdict(lambda: {"changes": 0, "additions": 0, "deletions": 0})
    for commit_file in commit_files:
        item = grouped[commit_file.file_id]
        item["changes"] = int(item["changes"]) + 1
        item["additions"] = int(item["additions"]) + commit_file.additions
        item["deletions"] = int(item["deletions"]) + commit_file.deletions

    for file_id, item in grouped.items():
        file_record = file_lookup[file_id]
        rows.append(
            {
                "path": file_record.path,
                "changes": item["changes"],
                "additions": item["additions"],
                "deletions": item["deletions"],
                "last_seen": short_date(file_record.last_seen_at),
            }
        )

    rows.sort(key=lambda entry: (-int(entry["changes"]), str(entry["path"]).lower()))
    most_added = sorted(rows, key=lambda entry: (-int(entry["additions"]), str(entry["path"]).lower()))
    most_deleted = sorted(rows, key=lambda entry: (-int(entry["deletions"]), str(entry["path"]).lower()))
    recent = sorted(rows, key=lambda entry: (entry["last_seen"], str(entry["path"]).lower()), reverse=True)
    inactive = sorted(rows, key=lambda entry: (entry["last_seen"], str(entry["path"]).lower()))
    return {
        "most_changed": rows,
        "most_added": most_added,
        "most_deleted": most_deleted,
        "recent": recent,
        "inactive": inactive,
    }


def _commit_row(commit: CommitRecord) -> dict[str, object]:
    return {
        "sha": commit.sha[:12],
        "date": short_date(commit.committed_at),
        "message": commit.message,
        "size": commit.additions + commit.deletions,
        "changed_files": commit.changed_files,
    }


def _commit_size_distribution(commits: list[CommitRecord]) -> dict[str, int]:
    buckets = {
        "0-9": 0,
        "10-49": 0,
        "50-199": 0,
        "200-499": 0,
        "500+": 0,
    }
    for commit in commits:
        size = commit.additions + commit.deletions
        if size < 10:
            buckets["0-9"] += 1
        elif size < 50:
            buckets["10-49"] += 1
        elif size < 200:
            buckets["50-199"] += 1
        elif size < 500:
            buckets["200-499"] += 1
        else:
            buckets["500+"] += 1
    return buckets


def _peak_hour(commits: list[CommitRecord]) -> str:
    if not commits:
        return "N/A"
    hour_counts = Counter(commit.committed_at.hour for commit in commits)
    hour, _ = max(hour_counts.items(), key=lambda item: item[1])
    return f"{hour:02d}:00"


def _heatmap_cells(commits: list[CommitRecord]) -> list[HeatmapCell]:
    today = date.today()
    start = today - timedelta(days=364)
    counts = Counter(commit.committed_at.date().isoformat() for commit in commits)
    cells: list[HeatmapCell] = []
    current = start
    while current <= today:
        delta = (current - start).days
        cells.append(
            HeatmapCell(
                date=current.isoformat(),
                week=delta // 7,
                weekday=current.weekday(),
                value=counts.get(current.isoformat(), 0),
            )
        )
        current += timedelta(days=1)
    return cells


def _age_days(first_commit_at: datetime | None, last_commit_at: datetime | None) -> int:
    if not first_commit_at or not last_commit_at:
        return 0
    return max((last_commit_at.date() - first_commit_at.date()).days, 0)
