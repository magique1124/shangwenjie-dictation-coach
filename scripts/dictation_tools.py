#!/usr/bin/env python3
"""Deterministic helpers for shangwenjie-dictation-coach.

The script intentionally uses only the Python standard library. It aligns a
learner's dictation with a source transcript, builds printable HTML practice
sheets, stores daily records in an Obsidian-compatible Markdown vault, and
builds weekly/monthly summary tables.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import html
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


WORD_RE = re.compile(r"\w+(?:['’\-]\w+)*|[^\w\s]", re.UNICODE)
TIMESTAMP_RE = re.compile(r"^\s*(?:\[(?P<ts1>\d{1,2}:\d{2}(?::\d{2})?)\]|(?P<ts2>\d{1,2}:\d{2}(?::\d{2})?))\s*")

CATEGORY_COLORS = {
    "omission": "#d73a49",
    "misheard": "#b08800",
    "weak_form": "#0969da",
    "linking": "#0969da",
    "vocabulary": "#8250df",
    "phrase": "#8250df",
    "grammar": "#6a737d",
    "spelling": "#1a7f37",
    "extra": "#d73a49",
    "unclassified": "#6a737d",
}

CATEGORY_LABELS = {
    "omission": "漏听",
    "misheard": "误听",
    "weak_form": "弱读/略读",
    "linking": "连读/同化",
    "vocabulary": "词汇问题",
    "phrase": "词组/地道表达",
    "grammar": "句法或逻辑",
    "spelling": "拼写问题",
    "extra": "多写",
    "unclassified": "待判断",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_word(word: str) -> str:
    normalized = unicodedata.normalize("NFKD", word)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^\w]", "", normalized, flags=re.UNICODE).casefold()


def split_words(text: str) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    line_start = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        offset = line_start
        ts_match = TIMESTAMP_RE.match(line)
        timestamp = None
        search_start = 0
        if ts_match:
            timestamp = ts_match.group("ts1") or ts_match.group("ts2")
            search_start = ts_match.end()
        for match in WORD_RE.finditer(line, search_start):
            token = match.group(0)
            if not normalize_word(token):
                continue
            words.append(
                {
                    "text": token,
                    "norm": normalize_word(token),
                    "start": offset + match.start(),
                    "end": offset + match.end(),
                    "line": line_no,
                    "timestamp": timestamp,
                }
            )
        line_start += len(line) + 1
    return words


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _classification_for_replacement(source_token: str, dictation_token: str) -> str:
    source_norm = normalize_word(source_token)
    dictation_norm = normalize_word(dictation_token)
    if source_norm == dictation_norm:
        return "spelling"
    if len(source_norm) == len(dictation_norm) and _edit_distance(source_norm, dictation_norm) == 1:
        return "spelling"
    return "misheard"


def align_texts(source_text: str, dictation_text: str, annotations: dict[str, Any] | None = None) -> dict[str, Any]:
    source_tokens = split_words(source_text)
    dictation_tokens = split_words(dictation_text)
    matcher = difflib.SequenceMatcher(
        a=[token["norm"] for token in source_tokens],
        b=[token["norm"] for token in dictation_tokens],
        autojunk=False,
    )
    errors: list[dict[str, Any]] = []
    correct_ranges: list[tuple[int, int]] = []
    error_index = 1

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            correct_ranges.append((i1, i2))
            continue
        source_slice = source_tokens[i1:i2]
        dictation_slice = dictation_tokens[j1:j2]
        if tag == "delete":
            for source_token in source_slice:
                category = "omission"
                note = "原文中有该词，但听写稿中没有。"
                errors.append(
                    _make_error(error_index, category, source_token, None, note, annotations)
                )
                error_index += 1
        elif tag == "insert":
            for dictation_token in dictation_slice:
                category = "extra"
                note = "听写稿中出现了原文没有的内容。"
                errors.append(
                    _make_error(error_index, category, None, dictation_token, note, annotations)
                )
                error_index += 1
        else:
            pair_count = max(len(source_slice), len(dictation_slice))
            for pos in range(pair_count):
                source_token = source_slice[pos] if pos < len(source_slice) else None
                dictation_token = dictation_slice[pos] if pos < len(dictation_slice) else None
                if source_token and dictation_token:
                    category = _classification_for_replacement(source_token["text"], dictation_token["text"])
                    note = "听到的形式与原文不一致。"
                elif source_token:
                    category = "omission"
                    dictation_token = None
                    note = "原文中有该词，但听写稿中没有。"
                else:
                    category = "extra"
                    source_token = None
                    note = "听写稿中出现了原文没有的内容。"
                errors.append(_make_error(error_index, category, source_token, dictation_token, note, annotations))
                error_index += 1

    source_words = len(source_tokens)
    dictation_words = len(dictation_tokens)
    counts = Counter(error["category"] for error in errors)
    return {
        "version": 1,
        "source_word_count": source_words,
        "dictation_word_count": dictation_words,
        "correct_ranges": correct_ranges,
        "errors": errors,
        "summary": {
            "error_count": len(errors),
            "category_counts": dict(sorted(counts.items())),
        },
    }


def _make_error(
    error_id: int,
    category: str,
    source_token: dict[str, Any] | None,
    dictation_token: dict[str, Any] | None,
    note: str,
    annotations: dict[str, Any] | None,
) -> dict[str, Any]:
    annotation = (annotations or {}).get(str(error_id), {})
    return {
        "id": error_id,
        "category": annotation.get("category", category),
        "source_text": source_token["text"] if source_token else None,
        "dictation_text": dictation_token["text"] if dictation_token else None,
        "source_start": source_token["start"] if source_token else None,
        "source_end": source_token["end"] if source_token else None,
        "source_line": source_token["line"] if source_token else None,
        "timestamp": source_token.get("timestamp") if source_token else None,
        "note": annotation.get("note", note),
        "diagnosis_confidence": annotation.get("confidence", "待结合原音频确认"),
    }


def sentence_chunks(text: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    line_start = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        clean = line.strip()
        if not clean:
            line_start += len(line) + 1
            continue
        timestamp_match = TIMESTAMP_RE.match(clean)
        timestamp = None
        body_start = 0
        if timestamp_match:
            timestamp = timestamp_match.group("ts1") or timestamp_match.group("ts2")
            body_start = timestamp_match.end()
        body = clean[body_start:].strip()
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", body) if part.strip()]
        cursor = body_start
        for part in parts:
            pos = line.find(part, cursor)
            if pos < 0:
                pos = body_start
            chunks.append(
                {
                    "text": part,
                    "line": line_no,
                    "timestamp": timestamp,
                    "start": line_start + pos,
                    "end": line_start + pos + len(part),
                }
            )
            cursor = pos + len(part)
        line_start += len(line) + 1
    return chunks


def annotated_source_html(source_text: str, alignment: dict[str, Any], include_dictation: bool = False, dictation_text: str = "") -> str:
    errors = sorted(
        [error for error in alignment.get("errors", []) if error.get("source_start") is not None],
        key=lambda item: (item["source_start"], item["source_end"]),
    )
    rendered: list[str] = []
    cursor = 0
    for error in errors:
        start = max(cursor, int(error["source_start"]))
        end = int(error["source_end"])
        if start > cursor:
            rendered.append(html.escape(source_text[cursor:start]))
        category = error.get("category", "unclassified")
        color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["unclassified"])
        label = CATEGORY_LABELS.get(category, category)
        replacement = error.get("dictation_text")
        detail = f"{label}: {error.get('source_text') or ''}"
        if replacement:
            detail += f" → 你写成 {replacement}"
        rendered.append(
            f'<mark class="error" style="background:{color}22;border-bottom:3px solid {color}" '
            f'title="{html.escape(detail)}">{html.escape(source_text[start:end])}</mark>'
        )
        cursor = end
    if cursor < len(source_text):
        rendered.append(html.escape(source_text[cursor:]))
    source_html = "".join(rendered)
    if not include_dictation:
        return source_html
    return source_html + (
        '<details><summary>查看你的听写稿</summary><pre class="dictation">'
        + html.escape(dictation_text)
        + "</pre></details>"
    )


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def build_daily_html(
    source_text: str,
    dictation_text: str,
    alignment: dict[str, Any],
    metadata: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
) -> str:
    diagnosis = diagnosis or {}
    title = metadata.get("title") or "今日听写练习"
    source_url = metadata.get("source_url") or ""
    category_counts = alignment.get("summary", {}).get("category_counts", {})
    count_items = "".join(
        f"<li>{html.escape(CATEGORY_LABELS.get(key, key))}: {value}</li>"
        for key, value in category_counts.items()
    ) or "<li>暂无错误记录</li>"
    expressions = metadata.get("expressions") or diagnosis.get("expressions") or []
    expression_rows = []
    for item in expressions:
        if isinstance(item, str):
            expression_rows.append(f"<li>{html.escape(item)}</li>")
        else:
            expression_rows.append(
                "<li><strong>{}</strong> — {}</li>".format(
                    html.escape(str(item.get("expression", ""))),
                    html.escape(str(item.get("meaning", item.get("note", "")))),
                )
            )
    chunks = sentence_chunks(source_text)
    chunk_rows = []
    for idx, chunk in enumerate(chunks, start=1):
        timestamp = f" @ {chunk['timestamp']}" if chunk.get("timestamp") else ""
        chunk_rows.append(
            f"""<section class="chunk">
              <div class="chunk-head">P{idx}{html.escape(timestamp)}</div>
              <p class="shadow-text">{html.escape(chunk['text'])}</p>
              <div class="drill">□ 不看稿听 2 遍　□ 慢速跟读 3 遍　□ 正常速度跟读 3 遍　□ 遮住原文复述</div>
            </section>"""
        )
    source_link = (
        f'<p><a href="{html.escape(source_url)}">打开原音频/视频</a></p>' if source_url else ""
    )
    diagnosis_html = diagnosis.get("html") or diagnosis.get("summary") or "请根据错误标记和原音频确认薄弱点。"
    tasks = diagnosis.get("tasks") or [
        "重点重听红色和蓝色标记处。",
        "遮住原文，复述今天最容易错的 3 句。",
        "用今天积累的表达各造一个新句。",
    ]
    task_rows = "".join(f"<li>□ {html.escape(str(task))}</li>" for task in tasks)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}｜每日听写跟读单</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.7; margin: 32px auto; max-width: 920px; color: #1f2328; }}
  h1, h2 {{ line-height: 1.25; }}
  .meta, .legend, .diagnosis, .tasks, .expressions {{ background: #f6f8fa; border-radius: 12px; padding: 14px 18px; }}
  .source {{ white-space: pre-wrap; font-size: 1.08rem; background: #fff; border: 1px solid #d0d7de; padding: 18px; border-radius: 10px; }}
  .chunk {{ border-left: 4px solid #0969da; padding: 10px 14px; margin: 12px 0; background: #f6f8fa; }}
  .chunk-head {{ font-size: .85rem; color: #57606a; font-weight: 700; }}
  .shadow-text {{ font-size: 1.12rem; margin: 6px 0; }}
  .drill {{ color: #57606a; font-size: .92rem; }}
  .dictation {{ white-space: pre-wrap; background: #fff; padding: 12px; border: 1px solid #d0d7de; }}
  mark.error {{ border-radius: 3px; padding: 0 2px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; }}
  @media print {{ body {{ margin: 12mm; }} a {{ color: inherit; text-decoration: none; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<h1>{html.escape(title)}｜每日听写跟读单</h1>
<div class="meta">
  <strong>日期：</strong>{html.escape(str(metadata.get("date", "")))}<br>
  <strong>领域：</strong>{html.escape(str(metadata.get("domain", "")))}<br>
  <strong>学习区间：</strong>{html.escape(str(metadata.get("segment", "")))}<br>
  <strong>材料时长：</strong>{html.escape(str(metadata.get("duration", "")))}
  {source_link}
</div>

<h2>一、原文错误标记</h2>
<div class="legend">颜色：红色=漏听；黄色=误听；蓝色=连读/弱读；紫色=词汇或词组；绿色=拼写；灰色=句法/逻辑。把鼠标放到标记上可查看详情。</div>
<div class="source">{annotated_source_html(source_text, alignment, include_dictation=True, dictation_text=dictation_text)}</div>

<h2>二、今日诊断</h2>
<div class="diagnosis">
  <p>{diagnosis_html}</p>
  <ul>{count_items}</ul>
</div>

<h2>三、跟读练习</h2>
{''.join(chunk_rows)}

<h2>四、今日值得积累</h2>
<div class="expressions"><ul>{''.join(expression_rows) or '<li>今天暂不新增表达，优先修复听力问题。</li>'}</ul></div>

<h2>五、完成清单</h2>
<div class="tasks"><ul>{task_rows}</ul></div>
</body>
</html>
"""


def build_final_html(
    source_text: str,
    alignment: dict[str, Any],
    metadata: dict[str, Any],
    session_records: Iterable[dict[str, Any]],
) -> str:
    records = list(session_records)
    dates = [str(record.get("date", "")) for record in records if record.get("date")]
    date_span = f"{min(dates)} — {max(dates)}" if dates else str(metadata.get("date", ""))
    category_counts = alignment.get("summary", {}).get("category_counts", {})
    rows = "".join(
        f"<tr><td>{html.escape(str(record.get('date', '')))}</td>"
        f"<td>{html.escape(str(record.get('segment', '')))}</td>"
        f"<td>{html.escape(str(record.get('learned_until', '')))}</td>"
        f"<td>{html.escape(str(record.get('main_weakness', '')))}</td></tr>"
        for record in records
    )
    counts = "".join(
        f"<li>{html.escape(CATEGORY_LABELS.get(key, key))}: {value}</li>"
        for key, value in category_counts.items()
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(str(metadata.get('title', '全文听写复盘')))}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.75;max-width:960px;margin:32px auto;color:#1f2328}}
.source{{white-space:pre-wrap;border:1px solid #d0d7de;padding:20px;border-radius:10px}}
mark.error{{border-radius:3px;padding:0 2px}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #d0d7de;padding:8px}}
@media print{{body{{margin:12mm}} a{{color:inherit;text-decoration:none}}}}
</style></head><body>
<h1>{html.escape(str(metadata.get('title', '全文听写复盘')))}</h1>
<p><strong>学习阶段：</strong>{html.escape(date_span)}</p>
<p><strong>材料：</strong>{html.escape(str(metadata.get('source_url', '')))}</p>
<h2>全文错误高亮</h2>
<div class="source">{annotated_source_html(source_text, alignment)}</div>
<h2>错误统计</h2><ul>{counts or '<li>暂无错误记录</li>'}</ul>
<h2>学习过程</h2>
<table><tr><th>日期</th><th>区间</th><th>学到</th><th>主要问题</th></tr>{rows}</table>
</body></html>"""


def material_slug(metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("material_id") or metadata.get("title") or "material")
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", raw).strip("-").lower()
    return slug or "material"


def save_session(
    vault_root: Path,
    metadata: dict[str, Any],
    alignment: dict[str, Any],
    dictation_text: str,
    learned_until: str | None,
    html_path: Path | None,
) -> dict[str, Any]:
    date = str(metadata.get("date") or dt.date.today().isoformat())
    slug = material_slug(metadata)
    material_dir = vault_root / "Materials" / slug
    daily_dir = material_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    progress_path = material_dir / "progress.json"
    progress = load_json(progress_path) if progress_path.exists() else {
        "material_id": slug,
        "title": metadata.get("title"),
        "source_url": metadata.get("source_url"),
        "status": "in_progress",
        "last_position": None,
        "sessions": [],
    }
    progress["title"] = metadata.get("title", progress.get("title"))
    progress["source_url"] = metadata.get("source_url", progress.get("source_url"))
    progress["last_updated"] = date
    if learned_until:
        progress["last_position"] = learned_until
        progress["progress_status"] = "confirmed"
    else:
        progress["progress_status"] = "unconfirmed"
    if metadata.get("status"):
        progress["status"] = metadata["status"]
    elif metadata.get("completed"):
        progress["status"] = "completed"
    if not any(session.get("date") == date and session.get("segment") == metadata.get("segment") for session in progress.get("sessions", [])):
        progress.setdefault("sessions", []).append(
            {
                "date": date,
                "segment": metadata.get("segment"),
                "learned_until": learned_until,
                "main_weakness": metadata.get("main_weakness"),
            }
        )
    write_json(progress_path, progress)

    counts = alignment.get("summary", {}).get("category_counts", {})
    frontmatter = [
        "---",
        f"material_id: {_yaml_scalar(slug)}",
        f"title: {_yaml_scalar(metadata.get('title'))}",
        f"date: {_yaml_scalar(date)}",
        f"segment: {_yaml_scalar(metadata.get('segment'))}",
        f"learned_until: {_yaml_scalar(learned_until)}",
        f"status: {_yaml_scalar(progress.get('status'))}",
        f"error_count: {alignment.get('summary', {}).get('error_count', 0)}",
        f"main_weakness: {_yaml_scalar(metadata.get('main_weakness'))}",
        "---",
        "",
        f"# {date} 听写学习记录",
        "",
        f"- 材料：{metadata.get('title', '')}",
        f"- 来源：{metadata.get('source_url', '')}",
        f"- 学习区间：{metadata.get('segment', '')}",
        f"- 今天学到：{learned_until or '未确认'}",
        f"- 主要问题：{metadata.get('main_weakness', '待诊断')}",
        "",
        "## 错误统计",
        "",
    ]
    frontmatter.extend(f"- {CATEGORY_LABELS.get(key, key)}：{value}" for key, value in counts.items())
    expressions = metadata.get("expressions") or []
    frontmatter.extend(["", "## 今日积累", ""])
    for item in expressions:
        if isinstance(item, str):
            frontmatter.append(f"- {item}")
        else:
            frontmatter.append(f"- **{item.get('expression', '')}**：{item.get('meaning', item.get('note', ''))}")
    if html_path:
        frontmatter.extend(["", "## 跟读练习单", "", f"- [{html_path.name}]({html_path.as_posix()})"])
    daily_path = daily_dir / f"{date}.md"
    daily_path.write_text("\n".join(frontmatter) + "\n", encoding="utf-8")

    record = {
        "date": date,
        "material_id": slug,
        "title": metadata.get("title"),
        "source_url": metadata.get("source_url"),
        "segment": metadata.get("segment"),
        "learned_until": learned_until,
        "status": progress.get("status"),
        "main_weakness": metadata.get("main_weakness"),
        "error_count": alignment.get("summary", {}).get("error_count", 0),
        "category_counts": counts,
        "new_expressions": expressions,
        "daily_note": daily_path.as_posix(),
        "html": html_path.as_posix() if html_path else None,
    }
    session_path = material_dir / "sessions.jsonl"
    with session_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"daily_note": str(daily_path), "progress": str(progress_path), "session_record": record}


def merge_alignments(paths: list[Path]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "version": 1,
        "source_word_count": None,
        "dictation_word_count": 0,
        "correct_ranges": [],
        "errors": [],
        "summary": {"error_count": 0, "category_counts": {}},
    }
    for path in paths:
        data = load_json(path)
        if merged["source_word_count"] is None:
            merged["source_word_count"] = data.get("source_word_count")
        merged["dictation_word_count"] += int(data.get("dictation_word_count", 0))
        merged["correct_ranges"].extend(data.get("correct_ranges", []))
        for error in data.get("errors", []):
            copied = dict(error)
            copied["id"] = len(merged["errors"]) + 1
            copied["source_file"] = path.name
            merged["errors"].append(copied)
    counts = Counter(error.get("category", "unclassified") for error in merged["errors"])
    merged["summary"] = {
        "error_count": len(merged["errors"]),
        "category_counts": dict(sorted(counts.items())),
    }
    return merged


def load_sessions(vault_root: Path, material_id: str | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    materials_root = vault_root / "Materials"
    if not materials_root.exists():
        return records
    for session_path in materials_root.glob("*/sessions.jsonl"):
        if material_id and session_path.parent.name != material_id:
            continue
        for line in session_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return sorted(records, key=lambda item: str(item.get("date", "")))


def build_period_report(vault_root: Path, period: str, output: Path, material_id: str | None = None) -> Path:
    records = load_sessions(vault_root, material_id)
    filtered: list[dict[str, Any]] = []
    for record in records:
        try:
            date = dt.date.fromisoformat(str(record.get("date")))
        except (TypeError, ValueError):
            continue
        if period == "weekly":
            current = date.isocalendar()
            now = dt.date.today().isocalendar()
            include = current[:2] == now[:2]
            label = f"{current.year}-W{current.week:02d}"
        else:
            now = dt.date.today()
            include = (date.year, date.month) == (now.year, now.month)
            label = f"{date.year}-{date.month:02d}"
        if include:
            filtered.append(record)
    if not filtered:
        raise SystemExit("没有找到当前周期的学习记录。")
    if period == "weekly":
        first = dt.date.fromisoformat(str(filtered[0]["date"]))
        label = f"{first.isocalendar().year}-W{first.isocalendar().week:02d}"
    else:
        first = dt.date.fromisoformat(str(filtered[0]["date"]))
        label = f"{first.year}-{first.month:02d}"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in filtered:
        counts = record.get("category_counts", {})
        category_text = "；".join(f"{CATEGORY_LABELS.get(key, key)} {value}" for key, value in counts.items())
        rows.append(
            f"| {record.get('date', '')} | {record.get('title', '')} | {record.get('segment', '')} | "
            f"{record.get('learned_until') or '未确认'} | {record.get('error_count', 0)} | "
            f"{category_text} | {record.get('main_weakness') or '待诊断'} |"
        )
    content = [
        f"# {label} 听写学习汇总",
        "",
        f"- 记录数：{len(filtered)}",
        f"- 材料数：{len(set(record.get('material_id') for record in filtered))}",
        f"- 错误总数：{sum(int(record.get('error_count', 0)) for record in filtered)}",
        "",
        "| 日期 | 材料 | 学习区间 | 学到 | 错误数 | 错误类型 | 主要问题 |",
        "|---|---|---|---|---:|---|---|",
        *rows,
        "",
    ]
    output.write_text("\n".join(content) + "\n", encoding="utf-8")
    csv_path = output.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "material", "segment", "learned_until", "error_count", "category_counts", "main_weakness"])
        for record in filtered:
            writer.writerow(
                [
                    record.get("date", ""),
                    record.get("title", ""),
                    record.get("segment", ""),
                    record.get("learned_until", ""),
                    record.get("error_count", 0),
                    json.dumps(record.get("category_counts", {}), ensure_ascii=False),
                    record.get("main_weakness", ""),
                ]
            )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    align = sub.add_parser("align", help="Align dictation with source transcript.")
    align.add_argument("--source", type=Path, required=True)
    align.add_argument("--dictation", type=Path, required=True)
    align.add_argument("--annotations", type=Path)
    align.add_argument("--output", type=Path, required=True)

    daily = sub.add_parser("daily-html", help="Build a printable daily practice sheet.")
    daily.add_argument("--source", type=Path, required=True)
    daily.add_argument("--dictation", type=Path, required=True)
    daily.add_argument("--alignment", type=Path, required=True)
    daily.add_argument("--metadata", type=Path, required=True)
    daily.add_argument("--diagnosis", type=Path)
    daily.add_argument("--output", type=Path, required=True)

    final = sub.add_parser("final-html", help="Build the final annotated transcript.")
    final.add_argument("--source", type=Path, required=True)
    final.add_argument("--alignment", type=Path, required=True)
    final.add_argument("--metadata", type=Path, required=True)
    final.add_argument("--vault-root", type=Path)
    final.add_argument("--output", type=Path, required=True)

    save = sub.add_parser("save-session", help="Save an Obsidian-compatible daily record.")
    save.add_argument("--vault-root", type=Path, required=True)
    save.add_argument("--metadata", type=Path, required=True)
    save.add_argument("--alignment", type=Path, required=True)
    save.add_argument("--dictation", type=Path, required=True)
    save.add_argument("--learned-until")
    save.add_argument("--html", type=Path)

    merge = sub.add_parser("merge-alignments", help="Merge segment alignments for a completed material.")
    merge.add_argument("--alignment", type=Path, action="append", required=True)
    merge.add_argument("--output", type=Path, required=True)

    report = sub.add_parser("report", help="Build a weekly or monthly Markdown/CSV report.")
    report.add_argument("--vault-root", type=Path, required=True)
    report.add_argument("--period", choices=["weekly", "monthly"], required=True)
    report.add_argument("--material-id")
    report.add_argument("--output", type=Path, required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "align":
        annotations = load_json(args.annotations) if args.annotations else {}
        result = align_texts(read_text(args.source), read_text(args.dictation), annotations)
        write_json(args.output, result)
    elif args.command == "daily-html":
        diagnosis = load_json(args.diagnosis) if args.diagnosis else {}
        result = build_daily_html(
            read_text(args.source),
            read_text(args.dictation),
            load_json(args.alignment),
            load_json(args.metadata),
            diagnosis,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    elif args.command == "final-html":
        metadata = load_json(args.metadata)
        session_records = load_sessions(args.vault_root, material_slug(metadata)) if args.vault_root else []
        result = build_final_html(read_text(args.source), load_json(args.alignment), metadata, session_records)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    elif args.command == "save-session":
        result = save_session(
            args.vault_root,
            load_json(args.metadata),
            load_json(args.alignment),
            read_text(args.dictation),
            args.learned_until,
            args.html,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "merge-alignments":
        write_json(args.output, merge_alignments(args.alignment))
    elif args.command == "report":
        output = build_period_report(args.vault_root, args.period, args.output, args.material_id)
        print(str(output))


if __name__ == "__main__":
    main()
