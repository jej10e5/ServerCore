---
name: analyze-git-diff-html
description: Analyze the current local Git working tree against the repository baseline and create readable HTML documentation. Use when the user asks in Korean or English to analyze, summarize, review, or document local changes/diffs, especially with phrases like "변경점 분석", "diff 정리", "수정사항 요약", "커밋 전 확인", or "make an HTML report of changes". Change reports must go under document/changes/, and completed large feature behavior may also require architecture HTML under document/architecture/.
---

# Analyze Git Diff HTML

## Overview

Create an HTML report that compares the repository baseline with current local changes. The report should explain what features or behaviors were added or changed, not list every file mechanically.

When the diff shows that one large behavior or feature unit is complete, also create or update an architecture document in `document/architecture/`.

## Workflow

1. Confirm the current working directory is the project root or locate it with `git rev-parse --show-toplevel`.
2. Run `scripts/generate_git_diff_report.py` from this skill:

```powershell
<python> .codex/skills/analyze-git-diff-html/scripts/generate_git_diff_report.py --repo <repo-root>
```

3. The script creates `document/changes/YYYYMMDD_HHMMSS_git_diff_report.html`.
4. Read the generated change report and inspect the diff enough to identify whether a complete large behavior was added or changed.
5. Run an architecture audit before finishing. Treat completed feature groups such as memory management, thread/lock management, networking, protocol flow, or server/client execution flow as architecture-document candidates.
6. If a complete large behavior exists, create or update an architecture HTML document in `document/architecture/`. Do not consider the task complete until this audit has either produced/updated the architecture document or explicitly determined that no architecture candidate exists.
7. Report the generated `changes` path and any `architecture` path to the user.

## Change Report Requirements

- Place generated change reports in `document/changes/` at the repository root.
- Use a timestamp-based filename so reports do not overwrite each other.
- Compare `HEAD` to the local working tree when `HEAD` exists. Include staged, unstaged, and untracked non-ignored files.
- If the repository has no commits yet, compare staged content and untracked files against an empty baseline.
- Put a concise "핵심 요약" sentence directly under the page title.
- In the summary area, state which features or behavior units were added or changed.
- Do not show a changed-file list as a main section.
- Do not add an explanatory bridge section such as "기능별 분석: 파일을 하나씩 나열하지 않고...".
- Organize the body by feature/behavior, not by file.
- For each feature, quote multiple core code fragments when the behavior spans multiple files. Each code block must have a small source-file caption below it.
- Every quoted code block must have its own analysis explaining what that exact code fragment is responsible for.
- If several quoted fragments cooperate, add a short grouped analysis explaining how those fragments work together.
- Render code snippets like a Visual Studio C++ editor view: dark editor background, C++ syntax colors, no raw Git diff markers like `+`, `-`, `@@`, `diff --git`, `---`, or `+++`.
- Do not write a large sentence such as "대표 코드: <file>에서..." before code blocks.
- Explain what role each feature plays and why each quoted code piece matters. Do not replace per-code analysis with a generic sentence like "위 코드 조각들은 핵심 지점입니다".
- Exclude generated documentation reports and the skill's own implementation files from normal change analysis unless the user specifically asks to analyze the documentation system itself.
- Keep generated HTML self-contained with inline CSS and no external dependencies.

## Architecture Document Rules

Create or update `document/architecture/*.html` only when the diff represents a completed large unit of behavior, such as a memory allocator subsystem, thread manager, locking/deadlock profiler, networking pipeline, game server flow, client/server protocol, or another coherent project-level feature.

Architecture audit rule:

- Always check the feature groups in the generated change report before replying.
- If a feature group has several cooperating source files and a coherent runtime responsibility, write or update an architecture document.
- Memory management and thread/lock management are architecture-worthy when their core files are present, even during an initial commit.
- Prefer stable feature filenames such as `memory-system.html` and `thread-locking.html` over timestamped duplicates.

Before writing an architecture document:

1. List existing files in `document/architecture/`.
2. If an existing document covers the same feature, update that file instead of creating a duplicate.
3. If no matching document exists, create a new timestamped or feature-named HTML file, for example `memory-system.html` or `20260617_101530_memory-system.html`.

Architecture HTML must include:

- title at the top and a left navigation panel
- one-line 핵심 요약 near the top
- purpose and responsibilities of the feature
- involved files/classes/functions
- data flow or call flow using visual sections, tables, and simple diagrams
- important Visual Studio-style C++ code snippets with small file captions below
- how the current diff changed or completed the behavior
- verification points or risks if they are inferable from the diff

Prefer updating existing architecture docs in place. Preserve useful previous content, revise stale sections, and add a "최근 변경" section when the current diff meaningfully changes the feature.

## Analysis Style

- Write in Korean unless the user asks otherwise.
- Prefer practical commit-review language: "추가된 기능", "핵심 역할", "영향 범위", "확인 포인트", and "주의할 점".
- Do not dump enormous diffs or every file body. Quote only the smallest code portions needed to explain the behavior.
- Mention ignored build/cache/user files only if they are relevant to the change set.
- When risk is unclear, say it is an inference from the diff.

## Script

Use `scripts/generate_git_diff_report.py` for deterministic change report creation. Architecture documents require agent judgment and should be created or updated after reviewing the generated change report and the actual diff.
