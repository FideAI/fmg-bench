"""Report generation for the system benchmark."""

from __future__ import annotations

from .models import SystemBenchmarkRun
from .publication import publication_mode_name, terminology_mapping_rows


def _append_failure_counts(lines: list[str], counts: dict[str, int], empty_message: str) -> None:
    if not counts:
        lines.append(empty_message)
        return
    for tag, count in counts.items():
        lines.append(f"- `{tag}`: {count}")


def build_markdown_report(run: SystemBenchmarkRun) -> str:
    """Render a concise markdown report for one system benchmark run."""
    summary = run.summary
    lines = [
        "# System Benchmark Report",
        "",
        f"- Model: `{run.model_id}`",
        f"- Judge Panel: `{run.judge_model}`",
        f"- Scenarios: `{run.scenario_count}`",
        f"- Completed items: `{summary.get('run_stats', {}).get('completed_items', len(run.evaluations))}`",
        f"- Failed items: `{summary.get('run_stats', {}).get('failed_items', len(run.failed_items))}`",
        "",
        "## Bottom Line",
        "",
        (
            "This report compares raw model behavior against structured-harness conditions to test "
            "configuration, grounding, comparison, and escalation behavior."
        ),
        "",
        "## Publication Terminology",
        "",
        "| Internal Mode | Publication Mode | Definition |",
        "|---|---|---|",
    ]
    for row in terminology_mapping_rows():
        lines.append(
            f"| `{row['internal_mode_name']}` | `{row['publication_mode_name']}` | {row['definition']} |"
        )
    lines.extend(
        [
        "",
        "## Run Health",
        "",
        f"- Completion rate: `{summary.get('run_stats', {}).get('completion_rate', 1.0):.2%}`",
        "",
        "## Mode Averages",
        "",
        "| Mode | Publication Mode | Weighted Score | Triage-Adjusted Score |",
        "|---|---|---:|---:|",
        ]
    )
    for mode, score in summary.get("mode_averages", {}).items():
        adjusted = summary.get("mode_triage_adjusted_averages", {}).get(mode, score)
        lines.append(
            f"| `{mode}` | `{publication_mode_name(mode)}` | {score:.2f} | {adjusted:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Average Deltas",
            "",
            "| Comparison | Publication Comparison | Weighted Score Delta | Triage-Adjusted Delta |",
            "|---|---|---:|---:|",
        ]
    )
    for pair, delta in summary.get("delta_summary", {}).get("weighted_score_delta", {}).items():
        adjusted = (
            summary.get("delta_summary", {}).get("triage_adjusted_score_delta", {}).get(pair, delta)
        )
        to_mode, _, from_mode = pair.partition("_minus_")
        public_pair = f"{publication_mode_name(to_mode)} minus {publication_mode_name(from_mode)}"
        lines.append(f"| `{pair}` | `{public_pair}` | {delta:+.2f} | {adjusted:+.2f} |")

    lines.extend(["", "## Triage Aggregates", ""])
    for level, values in summary.get("triage_level_adjusted_aggregates", {}).items():
        lines.append(f"### `{level}`")
        lines.append("")
        lines.append("| Mode | Publication Mode | Triage-Adjusted Avg |")
        lines.append("|---|---|---:|")
        for mode, score in values.items():
            lines.append(f"| `{mode}` | `{publication_mode_name(mode)}` | {score:.2f} |")
        lines.append("")

    compare_split = summary.get("compare_mode_triage_split", {})
    lines.extend(
        [
            "## Compare Mode Triage Split",
            "",
            "| Slice | Triage-Adjusted Avg |",
            "|---|---:|",
        ]
    )
    for slice_name in ("primary", "secondary_tertiary"):
        value = compare_split.get(slice_name)
        if value is None:
            lines.append(f"| `{slice_name}` | n/a |")
        else:
            lines.append(f"| `{slice_name}` | {value:.2f} |")

    lines.extend(["", "## Doctrine Locus Aggregates", ""])
    for locus, values in summary.get("doctrine_locus_aggregates", {}).items():
        lines.append(f"### `{locus}`")
        lines.append("")
        lines.append("| Mode | Publication Mode | Triage-Adjusted Avg |")
        lines.append("|---|---|---:|")
        for mode, score in values.items():
            lines.append(f"| `{mode}` | `{publication_mode_name(mode)}` | {score:.2f} |")
        lines.append("")

    robustness = summary.get("robustness", {})
    lines.extend(
        [
            "",
            "## Robustness And Stability",
            "",
            (
                "Stability is reported separately from quality. It estimates how much a mode's weighted "
                "score moves from the base scenario to perturbation variants; higher is more stable."
            ),
            "",
            "| Mode | Publication Mode | Stability Score |",
            "|---|---|---:|",
        ]
    )
    for mode, score in robustness.get("mode_stability_averages", {}).items():
        lines.append(f"| `{mode}` | `{publication_mode_name(mode)}` | {score:.2f} |")
    if not robustness.get("mode_stability_averages"):
        lines.append("| n/a | n/a | n/a |")

    lines.extend(["", "## Family Aggregates", ""])
    for family, values in summary.get("family_aggregates", {}).items():
        lines.append(f"### `{family}`")
        lines.append("")
        lines.append("| Mode | Publication Mode | Avg Score |")
        lines.append("|---|---|---:|")
        for mode, score in values.items():
            lines.append(f"| `{mode}` | `{publication_mode_name(mode)}` | {score:.2f} |")
        lines.append("")

    lines.extend(["## Top Failure Modes", ""])
    for mode, counts in summary.get("failure_counts", {}).items():
        lines.append(f"### `{mode}`")
        lines.append("")
        _append_failure_counts(lines, counts, "- No failure tags recorded.")
        lines.append("")

    lines.extend(["## Failure Modes By Triage Level", ""])
    for level, mode_counts in summary.get("failure_counts_by_triage", {}).items():
        lines.append(f"### `{level}`")
        lines.append("")
        for mode, counts in mode_counts.items():
            lines.append(f"#### `{mode}`")
            _append_failure_counts(lines, counts, "- No failure tags recorded.")
            lines.append("")
        lines.append("")

    grounding_tags = {
        "fabricates_grounding",
        "fabricated_scripture",
        "verse_context_misuse",
        "hallucinated_theology",
        "hallucinated_source_claim",
        "false_premise_acceptance",
        "denominational_overclaiming",
    }
    lines.extend(["## Grounding And Hallucination Tags", ""])
    for mode, counts in summary.get("failure_counts", {}).items():
        filtered = {tag: count for tag, count in counts.items() if tag in grounding_tags}
        lines.append(f"### `{mode}`")
        lines.append("")
        if filtered:
            for tag, count in filtered.items():
                lines.append(f"- `{tag}`: {count}")
        else:
            lines.append("- No grounding/hallucination tags recorded.")
        lines.append("")

    if run.failed_items:
        lines.extend(["## Failed Items", ""])
        for item in run.failed_items[:20]:
            lines.append(
                f"- `{item['scenario_id']}` / `{item['mode']}` / `{item['status']}`: {item.get('error', '')}"
            )
        if len(run.failed_items) > 20:
            lines.append(f"- ... and {len(run.failed_items) - 20} more")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
