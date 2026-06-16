#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import re
import subprocess
from pathlib import Path


MAX_CODE_LINES = 34
MAX_SNIPPETS_PER_FEATURE = 4
EXCLUDED_PREFIXES = (".codex/", "document/", ".vs/")
SOURCE_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
PROJECT_EXTENSIONS = {".sln", ".vcxproj", ".filters", ".props", ".targets"}
TEXT_EXTENSIONS = SOURCE_EXTENSIONS | PROJECT_EXTENSIONS | {
    ".cs", ".java", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".xml",
    ".md", ".txt", ".yml", ".yaml", ".html", ".css", ".scss", ".sql",
    ".ini", ".gitignore"
}

CPP_KEYWORDS = {
    "auto", "bool", "break", "case", "catch", "char", "class", "const",
    "constexpr", "const_cast", "continue", "decltype", "default", "delete",
    "do", "double", "dynamic_cast", "else", "enum", "explicit", "extern",
    "false", "float", "for", "friend", "if", "inline", "int", "long",
    "mutable", "namespace", "new", "noexcept", "nullptr", "operator",
    "private", "protected", "public", "reinterpret_cast", "return", "short",
    "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
    "switch", "template", "this", "thread_local", "throw", "true", "try",
    "typedef", "typename", "union", "unsigned", "using", "virtual", "void",
    "volatile", "while"
}
CPP_TYPES = {
    "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
    "size_t", "wstring", "string", "vector", "list", "map", "set", "queue",
    "stack", "atomic", "mutex", "shared_ptr", "weak_ptr", "unique_ptr"
}

FEATURE_RULES = [
    {
        "id": "memory-system",
        "title": "메모리 관리 시스템",
        "keywords": ("memory", "allocator", "objectpool", "refcounting"),
        "summary": "커스텀 할당자, 메모리 풀, 객체 풀, 참조 카운팅으로 서버 코어의 메모리 사용 방식을 직접 제어하는 기반 기능입니다.",
        "role": "할당 비용을 줄이고 객체 생명주기를 코어 계층에서 일관되게 다루도록 돕습니다.",
    },
    {
        "id": "thread-locking",
        "title": "스레드와 락 관리",
        "keywords": ("threadmanager", "lock", "deadlock", "coretls"),
        "summary": "스레드 등록/실행 흐름과 락 사용 패턴을 관리하고 데드락 가능성을 추적하는 동시성 기반 기능입니다.",
        "role": "멀티스레드 서버에서 실행 주체와 동기화 규칙을 명확하게 유지합니다.",
    },
    {
        "id": "core-foundation",
        "title": "코어 공통 기반",
        "keywords": ("coreglobal", "coremacro", "types", "typecast", "corepch", "pch", "container"),
        "summary": "전역 객체, 타입 정의, 타입 캐스팅 유틸리티, 공통 include를 묶어 서버 코어 전반에서 재사용하는 기반 기능입니다.",
        "role": "각 모듈이 같은 타입/매크로/전역 상태 규칙을 공유하게 해 코드 일관성을 높입니다.",
    },
    {
        "id": "server-client-apps",
        "title": "서버/클라이언트 실행 프로젝트",
        "keywords": ("gameserver", "dummyclient"),
        "summary": "GameServer와 DummyClient 실행 프로젝트를 구성해 코어 라이브러리를 사용하는 테스트/실행 진입점을 마련합니다.",
        "role": "서버 코어가 실제 실행 프로젝트에서 연결되는 지점을 제공합니다.",
    },
    {
        "id": "build-configuration",
        "title": "빌드 구성",
        "keywords": (".sln", ".vcxproj", ".filters"),
        "summary": "Visual Studio 솔루션과 프로젝트 파일로 빌드 대상, 소스 포함 관계, 프로젝트 구성을 정의합니다.",
        "role": "소스가 IDE와 빌드 시스템에서 올바르게 컴파일되도록 연결합니다.",
    },
    {
        "id": "git-hygiene",
        "title": "Git 추적 대상 정리",
        "keywords": (".gitignore",),
        "summary": "Visual Studio 임시 파일과 빌드 산출물을 커밋 대상에서 제외해 커밋을 소스 중심으로 유지합니다.",
        "role": "커밋 노이즈를 줄이고 저장소에 필요한 파일만 남기도록 돕습니다.",
    },
]


def run_git(repo, args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def repo_root(start):
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError("Not inside a Git repository.")
    return Path(result.stdout.strip())


def has_head(repo):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def is_reportable_path(path):
    normalized = path.replace("\\", "/")
    return not any(normalized.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def is_text_path(path):
    return Path(path).suffix.lower() in TEXT_EXTENSIONS or Path(path).name == ".gitignore"


def parse_name_status(text):
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        path = parts[-1]
        if is_reportable_path(path):
            rows.append({"status": parts[0], "path": path})
    return rows


def parse_numstat(text):
    stats = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        if not is_reportable_path(path):
            continue
        try:
            stats[path] = {"added": int(added), "deleted": int(deleted)}
        except ValueError:
            stats[path] = {"added": 0, "deleted": 0}
    return stats


def parse_status(repo):
    status_by_path = {}
    for line in run_git(repo, ["status", "--porcelain=v1"]).splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if is_reportable_path(path):
            status_by_path[path] = line[:2]
    return status_by_path


def untracked_files(repo):
    return [
        path for path in (line.strip() for line in run_git(repo, ["ls-files", "--others", "--exclude-standard"]).splitlines())
        if path and is_reportable_path(path)
    ]


def split_patch_by_file(patch):
    sections = {}
    current_path = None
    current_lines = []
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if current_path:
                sections[current_path] = "\n".join(current_lines)
            current_lines = [line]
            parts = line.split(" b/", 1)
            current_path = parts[1] if len(parts) == 2 else line
        else:
            current_lines.append(line)
    if current_path:
        sections[current_path] = "\n".join(current_lines)
    return {path: text for path, text in sections.items() if is_reportable_path(path)}


def read_untracked_text(repo, rel_path):
    path = repo / rel_path
    if not path.is_file() or not is_text_path(rel_path):
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def cxx_snippet_from_diff(diff_text):
    code = []
    for raw in diff_text.splitlines():
        if raw.startswith(("diff --git", "index ", "--- ", "+++ ", "new file mode", "deleted file mode", "@@")):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line = raw[1:]
        elif raw.startswith(" ") and raw.strip():
            line = raw[1:]
        else:
            continue
        if line.strip() or code:
            code.append(line)
        if len(code) >= MAX_CODE_LINES:
            break
    return trim_code_block(code)


def cxx_snippet_from_text(text):
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("class ", "struct ", "template", "void ", "int ", "Type*", "static ", "#include")):
            start = i
            break
    return trim_code_block(lines[start:start + MAX_CODE_LINES])


def trim_code_block(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) if lines else "// 대표 코드 없음"


def highlight_cpp(code):
    return "\n".join(highlight_cpp_line(line) for line in code.splitlines())


def highlight_cpp_line(line):
    stripped = line.lstrip()
    leading = line[:len(line) - len(stripped)]
    if stripped.startswith("#"):
        return html.escape(leading) + f'<span class="tok-pp">{html.escape(stripped)}</span>'

    result = [html.escape(leading)]
    i = len(leading)
    while i < len(line):
        if line.startswith("//", i):
            result.append(f'<span class="tok-comment">{html.escape(line[i:])}</span>')
            break

        ch = line[i]
        if ch in {'"', "'"}:
            end = i + 1
            escaped = False
            while end < len(line):
                if line[end] == ch and not escaped:
                    end += 1
                    break
                escaped = line[end] == "\\" and not escaped
                if line[end] != "\\":
                    escaped = False
                end += 1
            result.append(f'<span class="tok-string">{html.escape(line[i:end])}</span>')
            i = end
            continue

        number = re.match(r"\d+(\.\d+)?", line[i:])
        if number:
            value = number.group(0)
            result.append(f'<span class="tok-number">{html.escape(value)}</span>')
            i += len(value)
            continue

        ident = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[i:])
        if ident:
            value = ident.group(0)
            if value in CPP_KEYWORDS:
                result.append(f'<span class="tok-keyword">{html.escape(value)}</span>')
            elif value in CPP_TYPES or (value[:1].isupper() and len(value) > 1):
                result.append(f'<span class="tok-type">{html.escape(value)}</span>')
            else:
                result.append(html.escape(value))
            i += len(value)
            continue

        result.append(html.escape(ch))
        i += 1
    return "".join(result)


def status_label(status):
    if status == "??":
        return "신규"
    if status.startswith("A"):
        return "추가"
    if status.startswith("M") or "M" in status:
        return "수정"
    if status.startswith("D") or "D" in status:
        return "삭제"
    if status.startswith("R"):
        return "이름 변경"
    return status.strip() or "변경"


def feature_for_path(path):
    lowered = path.lower().replace("\\", "/")
    for rule in FEATURE_RULES:
        if any(keyword in lowered for keyword in rule["keywords"]):
            return rule
    return {
        "id": "misc",
        "title": "기타 프로젝트 구성",
        "summary": "주요 기능 그룹에 직접 속하지 않는 보조 변경입니다.",
        "role": "프로젝트 구성이나 보조 코드의 완성도를 높이는 역할을 합니다.",
    }


def file_score(file):
    path = file["path"]
    ext = Path(path).suffix.lower()
    score = file["added"] + file["deleted"]
    if ext in SOURCE_EXTENSIONS:
        score += 120
    elif ext in PROJECT_EXTENSIONS:
        score += 30
    if Path(path).name == ".gitignore":
        score += 20
    return score


def collect_changes(repo):
    if has_head(repo):
        base_desc = "HEAD 대비 현재 로컬 변경사항"
        name_status = parse_name_status(run_git(repo, ["diff", "HEAD", "--name-status", "--"]))
        numstat = parse_numstat(run_git(repo, ["diff", "HEAD", "--numstat", "--"]))
        patch_by_file = split_patch_by_file(run_git(repo, ["diff", "HEAD", "--patch", "--"]))
    else:
        base_desc = "첫 커밋 전 상태: 스테이징/신규 파일 기준"
        name_status = parse_name_status(run_git(repo, ["diff", "--cached", "--name-status", "--"]))
        numstat = parse_numstat(run_git(repo, ["diff", "--cached", "--numstat", "--"]))
        patch_by_file = split_patch_by_file(run_git(repo, ["diff", "--cached", "--patch"]))

    tracked_by_path = {row["path"]: row for row in name_status}
    for path in untracked_files(repo):
        tracked_by_path.setdefault(path, {"status": "??", "path": path})

    status_by_path = parse_status(repo)
    files = []
    for path, row in sorted(tracked_by_path.items(), key=lambda item: item[0].lower()):
        stat = numstat.get(path, {"added": 0, "deleted": 0})
        raw_diff = patch_by_file.get(path, "")
        raw_text = ""
        if row["status"] == "??":
            raw_text = read_untracked_text(repo, path)
            if raw_text and not stat["added"]:
                stat["added"] = len(raw_text.splitlines())

        snippet = cxx_snippet_from_diff(raw_diff) if raw_diff else cxx_snippet_from_text(raw_text)
        feature = feature_for_path(path)
        files.append({
            "path": path,
            "status": status_by_path.get(path, row["status"]),
            "label": status_label(status_by_path.get(path, row["status"])),
            "added": stat["added"],
            "deleted": stat["deleted"],
            "snippet": snippet,
            "feature": feature,
        })
    return base_desc, files


def group_features(files):
    grouped = {}
    for file in files:
        feature = file["feature"]
        item = grouped.setdefault(feature["id"], {
            "id": feature["id"],
            "title": feature["title"],
            "summary": feature["summary"],
            "role": feature["role"],
            "files": [],
            "added": 0,
            "deleted": 0,
        })
        item["files"].append(file)
        item["added"] += file["added"]
        item["deleted"] += file["deleted"]

    features = list(grouped.values())
    features.sort(key=lambda f: (f["added"] + f["deleted"], len(f["files"])), reverse=True)
    for feature in features:
        feature["files"].sort(key=file_score, reverse=True)
        feature["snippets"] = pick_feature_snippets(feature["files"])
    return features


def pick_feature_snippets(files):
    picked = []
    seen_stems = set()
    for file in files:
        if not file["snippet"].strip():
            continue
        stem = Path(file["path"]).stem.lower()
        ext = Path(file["path"]).suffix.lower()
        if stem in seen_stems and len(picked) >= 2:
            continue
        if ext not in SOURCE_EXTENSIONS and picked and len(picked) >= 2:
            continue
        picked.append(file)
        seen_stems.add(stem)
        if len(picked) >= MAX_SNIPPETS_PER_FEATURE:
            break
    return picked or files[:1]


def html_id(text):
    safe = [ch if ch.isalnum() else "-" for ch in text]
    return "".join(safe).strip("-").lower()


def snippet_analysis(file):
    path = file["path"]
    lower = path.lower()
    stem = Path(path).stem.lower()

    if "refcounting" in stem:
        return "객체의 참조 수를 관리하고 참조 수가 0이 되는 시점에 객체를 삭제하는 소유권 관리 지점입니다."
    if stem == "memory":
        if path.endswith(".cpp"):
            return "요청 크기에 따라 메모리 풀을 사용할지 일반 aligned allocation을 사용할지 결정하는 중앙 분기입니다."
        return "xnew, xdelete, MakeShared 같은 객체 생성/해제 래퍼를 제공해 풀 할당과 placement new 사용을 한곳에 모읍니다."
    if "memorypool" in stem:
        return "고정 크기 메모리 블록을 SLIST에 보관했다가 재사용하는 캐시 계층입니다."
    if "allocator" in stem:
        return "외부 할당 요청을 GMemory 기반 풀 할당으로 연결하는 어댑터입니다."
    if "objectpool" in stem:
        return "메모리 블록이 아니라 객체 자체를 재사용하기 위한 객체 풀 계층입니다."
    if "threadmanager" in stem:
        return "스레드 생성 시 TLS를 초기화하고 콜백 실행 후 정리하는 실행 흐름의 진입점입니다."
    if stem == "lock":
        return "writer 소유권과 reader 카운트를 atomic flag로 관리하는 실제 동기화 지점입니다."
    if "deadlockprofiler" in stem:
        return "락 획득 순서를 그래프로 기록하고 cycle을 검사해 데드락 가능성을 감지합니다."
    if "coretls" in stem:
        return "스레드별 ID와 상태를 저장해 Lock과 ThreadManager가 같은 스레드 기준을 공유하게 합니다."
    if "typecast" in stem:
        return "타입 목록과 타입 ID를 구성해 런타임 타입 판별과 캐스팅 기반을 제공합니다."
    if "coreglobal" in stem:
        return "메모리, 스레드, 데드락 프로파일러 같은 코어 전역 객체를 생성하고 연결합니다."
    if "coremacro" in stem:
        return "assert, crash, lock guard 등 공통 매크로로 오류 처리와 반복 패턴을 통일합니다."
    if "gameserver" in lower:
        return "코어 라이브러리를 실제 서버 실행 프로젝트에서 사용하는 진입점 또는 예시입니다."
    if "dummyclient" in lower:
        return "더미 클라이언트 실행 프로젝트의 최소 진입점으로 서버와 분리된 실행 대상을 제공합니다."
    if path.endswith((".vcxproj", ".filters", ".sln")):
        return "Visual Studio가 어떤 소스와 프로젝트를 빌드에 포함할지 결정하는 구성입니다."
    if Path(path).name == ".gitignore":
        return "Visual Studio 임시 파일과 빌드 산출물이 Git 변경점에 섞이지 않도록 제외합니다."
    return "해당 기능을 구성하는 보조 코드 조각입니다. 주변 코드와 함께 역할을 해석해야 합니다."


def relationship_analysis(feature):
    fid = feature["id"]
    if fid == "memory-system":
        return "Memory가 할당 정책을 결정하고, MemoryPool이 작은 블록을 재사용하며, Allocator와 생성 래퍼가 호출 지점을 단순화합니다."
    if fid == "thread-locking":
        return "ThreadManager가 실행 환경을 만들고, Lock이 경합을 제어하며, DeadLockProfiler가 락 순서 그래프를 검증합니다."
    if fid == "core-foundation":
        return "타입, 매크로, 전역 객체, 공통 include가 함께 다른 기능들이 같은 규칙 위에서 컴파일되고 실행되도록 받칩니다."
    if fid == "server-client-apps":
        return "실행 프로젝트가 코어 라이브러리를 실제 프로그램 진입점에 연결해 이후 테스트와 확장의 기반이 됩니다."
    if fid == "build-configuration":
        return "솔루션/프로젝트/필터 파일이 소스 파일과 빌드 대상을 Visual Studio 구성에 연결합니다."
    if fid == "git-hygiene":
        return "Git 제외 규칙이 빌드 산출물과 개인 설정 파일을 분리해 커밋과 분석이 소스 변화에 집중되게 합니다."
    return "인용된 코드 조각들이 같은 기능 단위 안에서 역할을 나누어 동작합니다."


def code_panels(files):
    panels = []
    for file in files:
        panels.append(
            f"""
              <div class="code-panel">
                <pre><code class="language-cpp">{highlight_cpp(file['snippet'])}</code></pre>
                <div class="code-caption">{html.escape(file['path'])}</div>
                <div class="snippet-analysis"><strong>코드 역할:</strong> {html.escape(snippet_analysis(file))}</div>
              </div>
            """
        )
    return "".join(panels)


def build_report(repo):
    base_desc, files = collect_changes(repo)
    features = group_features(files)
    total_added = sum(file["added"] for file in files)
    total_deleted = sum(file["deleted"] for file in files)
    now = dt.datetime.now()
    feature_titles = ", ".join(feature["title"] for feature in features[:5]) or "변경 없음"
    headline = f"핵심 요약: {base_desc}으로 {feature_titles} 기능 변화가 확인되었습니다."

    nav_items = ['<a href="#summary">요약</a>']
    nav_items.extend(f'<a href="#{html_id(feature["id"])}">{html.escape(feature["title"])}</a>' for feature in features)

    feature_cards = []
    feature_sections = []
    for feature in features:
        feature_cards.append(
            f"""
            <div class="feature-card">
              <strong>{html.escape(feature['title'])}</strong>
              <p>{html.escape(feature['summary'])}</p>
              <span>관련 파일 {len(feature['files'])}개 · 코드 조각 {len(feature['snippets'])}개 · +{feature['added']} / -{feature['deleted']}</span>
            </div>
            """
        )
        feature_sections.append(
            f"""
            <section class="feature-section" id="{html_id(feature['id'])}">
              <div class="feature-heading">
                <h3>{html.escape(feature['title'])}</h3>
                <span class="badge">+{feature['added']} / -{feature['deleted']}</span>
              </div>
              <p class="analysis"><strong>추가된 기능:</strong> {html.escape(feature['summary'])}</p>
              <p class="analysis"><strong>핵심 역할:</strong> {html.escape(feature['role'])}</p>
              <div class="code-stack">{code_panels(feature['snippets'])}</div>
              <p class="relationship-analysis"><strong>함께 동작하는 방식:</strong> {html.escape(relationship_analysis(feature))}</p>
              <p class="analysis"><strong>분석:</strong> 위 코드 조각들은 이 기능을 구성하는 핵심 지점입니다. 여러 파일이 함께 동작하는 경우에는 할당, 소유권, 실행 흐름, 빌드 연결처럼 역할이 나뉘는 부분을 각각 인용했습니다.</p>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Git 변경점 분석 리포트</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #20242a;
      --muted: #667085;
      --line: #d9dee7;
      --accent: #1f6feb;
      --plus: #16833a;
      --minus: #c83f3f;
      --vs-bg: #1e1e1e;
      --vs-line: #2d2d30;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: var(--ink); background: var(--bg); }}
    .layout {{ display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }}
    nav {{ position: sticky; top: 0; height: 100vh; overflow: auto; padding: 24px 18px; background: #18202b; color: white; }}
    nav h2 {{ margin: 0 0 16px; font-size: 18px; }}
    nav a {{ display: block; color: #dbe7ff; text-decoration: none; padding: 8px 10px; border-radius: 6px; font-size: 13px; overflow-wrap: anywhere; }}
    nav a:hover {{ background: rgba(255,255,255,.1); }}
    main {{ padding: 34px; max-width: 1180px; }}
    h1 {{ margin: 0 0 10px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ margin-top: 34px; font-size: 24px; }}
    h3 {{ margin: 0; font-size: 20px; overflow-wrap: anywhere; }}
    .headline {{ margin: 0 0 22px; padding: 14px 16px; border-left: 5px solid var(--accent); background: #eaf2ff; font-weight: 700; }}
    .meta {{ color: var(--muted); margin-bottom: 22px; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 12px; }}
    .card, .feature-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .card strong {{ display: block; font-size: 26px; margin-bottom: 4px; }}
    .card span, .feature-card span {{ color: var(--muted); font-size: 13px; }}
    .feature-grid {{ display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 12px; margin-top: 14px; }}
    .feature-card strong {{ display: block; font-size: 17px; margin-bottom: 8px; }}
    .feature-card p {{ margin: 0 0 10px; line-height: 1.55; color: #344054; }}
    .feature-section {{ margin-top: 18px; padding: 18px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }}
    .feature-heading {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 10px; }}
    .analysis {{ line-height: 1.65; color: #344054; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: #eef4ff; color: #174ea6; font-size: 12px; font-weight: 700; white-space: nowrap; }}
    .code-stack {{ display: grid; gap: 14px; margin: 14px 0; }}
    .code-panel {{ border: 1px solid var(--vs-line); border-radius: 8px; overflow: hidden; background: var(--vs-bg); box-shadow: inset 0 1px 0 rgba(255,255,255,.04); }}
    pre {{ margin: 0; padding: 16px; background: var(--vs-bg); color: #d4d4d4; overflow: auto; max-height: 360px; line-height: 1.5; tab-size: 4; }}
    code {{ font-family: Consolas, "Cascadia Mono", monospace; font-size: 13px; }}
    .code-caption {{ padding: 7px 12px; border-top: 1px solid var(--vs-line); background: #252526; color: #9cdcfe; font-family: Consolas, "Cascadia Mono", monospace; font-size: 11px; }}
    .snippet-analysis {{ padding: 10px 12px 12px; border-top: 1px solid var(--vs-line); background: #202020; color: #d4d4d4; font-size: 13px; line-height: 1.55; }}
    .snippet-analysis strong {{ color: #dcdcaa; }}
    .relationship-analysis {{ line-height: 1.65; color: #344054; }}
    .feature-section > p.analysis:last-child {{ display: none; }}
    .tok-keyword {{ color: #569cd6; }}
    .tok-type {{ color: #4ec9b0; }}
    .tok-string {{ color: #ce9178; }}
    .tok-comment {{ color: #6a9955; }}
    .tok-number {{ color: #b5cea8; }}
    .tok-pp {{ color: #c586c0; }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{ position: relative; height: auto; }}
      main {{ padding: 22px; }}
      .cards, .feature-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <h2>목차</h2>
      {''.join(nav_items)}
    </nav>
    <main>
      <h1>Git 변경점 분석 리포트</h1>
      <p class="headline">{html.escape(headline)}</p>
      <p class="meta">생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')} · 기준: {html.escape(base_desc)} · 저장소: {html.escape(str(repo))}</p>

      <section id="summary">
        <h2>요약</h2>
        <div class="cards">
          <div class="card"><strong>{len(features)}</strong><span>기능 단위</span></div>
          <div class="card"><strong>{len(files)}</strong><span>관련 파일</span></div>
          <div class="card"><strong class="plus">+{total_added}</strong><span>추가 라인</span></div>
          <div class="card"><strong class="minus">-{total_deleted}</strong><span>삭제 라인</span></div>
        </div>
        <div class="feature-grid">{''.join(feature_cards)}</div>
      </section>

      {''.join(feature_sections)}
    </main>
  </div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate a feature-oriented HTML report for local Git diffs.")
    parser.add_argument("--repo", default=".", help="Repository root or any path inside it.")
    args = parser.parse_args()

    repo = repo_root(Path(args.repo).resolve())
    report = build_report(repo)
    out_dir = repo / "document" / "changes"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{timestamp}_git_diff_report.html"
    out_path.write_text(report, encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
