"""
File: log_message_trace.py
Suggested placement: tools/diagnostics/log_message_trace.py

python log_message_trace.py path/to/system.log
python log_message_trace.py path/to/system.log -o message_trace_report.txt
 
Standalone diagnostic utility for structured JSONL logs.

Version 1:
- Reads one JSONL log file.
- Groups entries by message_id.
- Sorts entries in each group by timestamp.
- Sorts groups by message_id.
- Reports missing message IDs.
- Flags possible duplicate entries.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

MISSING = "<missing>"


@dataclass(frozen=True)
class ParsedLogEntry:
    line_number: int
    raw: dict[str, Any]
    message_id: Optional[str]
    timestamp: Any
    human_timestamp: Optional[str]
    event_type: Optional[str]
    source_module: Optional[str]
    target_module: Optional[str]
    msg_type: Optional[str]
    severity: Optional[str]
    log_id: Optional[str]
    message: Optional[str]

    @classmethod
    def from_record(cls, line_number: int, record: dict[str, Any]) -> "ParsedLogEntry":
        return cls(
            line_number=line_number,
            raw=record,
            message_id=_as_optional_string(record.get("message_id")),
            timestamp=record.get("timestamp"),
            human_timestamp=_as_optional_string(record.get("human_timestamp")),
            event_type=_as_optional_string(record.get("event_type")),
            source_module=_as_optional_string(record.get("source_module")),
            target_module=_as_optional_string(record.get("target_module")),
            msg_type=_as_optional_string(record.get("msg_type")),
            severity=_as_optional_string(record.get("severity")),
            log_id=_as_optional_string(record.get("log_id")),
            message=_as_optional_string(record.get("message")),
        )


@dataclass(frozen=True)
class ParseIssue:
    line_number: int
    reason: str
    text: str


def _as_optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _display(value: Any) -> str:
    return MISSING if value is None or value == "" else str(value)


def _timestamp_sort_key(value: Any) -> tuple[int, Any]:
    if isinstance(value, (int, float)):
        return 0, float(value)

    if isinstance(value, str):
        stripped = value.strip()
        try:
            return 0, float(stripped)
        except ValueError:
            pass

        try:
            return 1, datetime.fromisoformat(stripped.replace("Z", "+00:00"))
        except ValueError:
            return 2, stripped

    return 3, ""


def read_jsonl(path: Path) -> tuple[list[ParsedLogEntry], list[ParseIssue]]:
    entries: list[ParsedLogEntry] = []
    issues: list[ParseIssue] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(ParseIssue(line_number, f"Invalid JSON: {exc.msg}", stripped))
                continue

            if not isinstance(record, dict):
                issues.append(ParseIssue(line_number, "JSON value is not an object", stripped))
                continue

            entries.append(ParsedLogEntry.from_record(line_number, record))

    return entries, issues


def group_by_message_id(
    entries: Iterable[ParsedLogEntry],
) -> tuple[dict[str, list[ParsedLogEntry]], list[ParsedLogEntry]]:
    grouped: dict[str, list[ParsedLogEntry]] = defaultdict(list)
    missing: list[ParsedLogEntry] = []

    for entry in entries:
        if entry.message_id is None:
            missing.append(entry)
        else:
            grouped[entry.message_id].append(entry)

    for group in grouped.values():
        group.sort(key=lambda item: (_timestamp_sort_key(item.timestamp), item.line_number))

    return dict(grouped), missing


def duplicate_signature(entry: ParsedLogEntry) -> tuple[Any, ...]:
    return (
        entry.message_id,
        entry.timestamp,
        entry.event_type,
        entry.source_module,
        entry.target_module,
        entry.msg_type,
        entry.message,
    )


def find_possible_duplicates(
    entries: Iterable[ParsedLogEntry],
) -> list[list[ParsedLogEntry]]:
    buckets: dict[tuple[Any, ...], list[ParsedLogEntry]] = defaultdict(list)

    for entry in entries:
        buckets[duplicate_signature(entry)].append(entry)

    groups = [group for group in buckets.values() if len(group) > 1]
    groups.sort(
        key=lambda group: (
            _display(group[0].message_id),
            _timestamp_sort_key(group[0].timestamp),
        )
    )
    return groups


def format_entry(entry: ParsedLogEntry) -> list[str]:
    return [
        f"    Line:          {entry.line_number}",
        f"    Timestamp:     {_display(entry.timestamp)}",
        f"    Human time:    {_display(entry.human_timestamp)}",
        f"    Event type:    {_display(entry.event_type)}",
        f"    Message type:  {_display(entry.msg_type)}",
        f"    Source:        {_display(entry.source_module)}",
        f"    Target:        {_display(entry.target_module)}",
        f"    Severity:      {_display(entry.severity)}",
        f"    Log ID:        {_display(entry.log_id)}",
        f"    Message:       {_display(entry.message)}",
    ]


def build_report(
    path: Path,
    entries: list[ParsedLogEntry],
    parse_issues: list[ParseIssue],
) -> str:
    grouped, missing = group_by_message_id(entries)
    duplicates = find_possible_duplicates(entries)

    lines: list[str] = []
    separator = "=" * 88
    subsection = "-" * 88

    lines.extend([
        separator,
        "STRUCTURED LOG MESSAGE TRACE REPORT",
        separator,
        f"Input file:                 {path}",
        f"Parsed log entries:         {len(entries)}",
        f"Unique message IDs:         {len(grouped)}",
        f"Entries missing message ID: {len(missing)}",
        f"Possible duplicate groups:  {len(duplicates)}",
        f"Parse issues:               {len(parse_issues)}",
        "",
        separator,
        "MESSAGES SORTED BY MESSAGE ID",
        separator,
        "",
    ])

    if not grouped:
        lines.extend(["No entries containing a message_id were found.", ""])
    else:
        for message_id in sorted(grouped, key=str.casefold):
            group = grouped[message_id]
            lines.extend([
                f"Message ID: {message_id}",
                f"Occurrences: {len(group)}",
                subsection,
            ])
            for index, entry in enumerate(group, start=1):
                lines.append(f"  Entry {index}")
                lines.extend(format_entry(entry))
                lines.append("")
            lines.extend([separator, ""])

    lines.extend([separator, "ENTRIES MISSING MESSAGE ID", separator, ""])
    if not missing:
        lines.extend(["None.", ""])
    else:
        for entry in sorted(missing, key=lambda x: (_timestamp_sort_key(x.timestamp), x.line_number)):
            lines.extend(format_entry(entry))
            lines.append("")

    lines.extend([separator, "POSSIBLE DUPLICATE LOG ENTRIES", separator, ""])
    if not duplicates:
        lines.extend(["None.", ""])
    else:
        for number, group in enumerate(duplicates, start=1):
            first = group[0]
            lines.extend([
                f"Duplicate group {number}",
                f"Message ID: {_display(first.message_id)}",
                f"Count: {len(group)}",
                f"Lines: {', '.join(str(item.line_number) for item in group)}",
                f"Event type: {_display(first.event_type)}",
                f"Source: {_display(first.source_module)}",
                f"Target: {_display(first.target_module)}",
                f"Timestamp: {_display(first.timestamp)}",
                "",
            ])

    lines.extend([separator, "PARSE ISSUES", separator, ""])
    if not parse_issues:
        lines.extend(["None.", ""])
    else:
        for issue in parse_issues:
            lines.extend([
                f"Line:   {issue.line_number}",
                f"Reason: {issue.reason}",
                f"Text:   {issue.text}",
                "",
            ])

    return "\n".join(lines)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Group structured JSONL log entries by message_id."
    )
    parser.add_argument("log_file", type=Path, help="Path to the JSONL log file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output text file. Otherwise prints to the console.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    log_file: Path = args.log_file
    output_file: Optional[Path] = args.output

    if not log_file.exists():
        print(f"Error: log file does not exist: {log_file}", file=sys.stderr)
        return 1

    if not log_file.is_file():
        print(f"Error: path is not a file: {log_file}", file=sys.stderr)
        return 1

    try:
        entries, issues = read_jsonl(log_file)
        report = build_report(log_file, entries, issues)
    except OSError as exc:
        print(f"Error reading log file: {exc}", file=sys.stderr)
        return 1

    if output_file is None:
        print(report)
        return 0

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report, encoding="utf-8")
    except OSError as exc:
        print(f"Error writing report file: {exc}", file=sys.stderr)
        return 1

    print(f"Report written to: {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
