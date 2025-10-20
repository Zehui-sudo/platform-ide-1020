import re
from typing import List, Tuple, Dict


_EOL_RE = re.compile(r"\r\n?|\u2028|\u2029")
_TRAILING_SEMI_RE = re.compile(r";[ \t]*(?=\n|$)")

# Quoted edge labels -> pipe syntax
_EDGE_QUOTED_REPLACERS = [
    (re.compile(r"--\s*\"([^\"]*?)\"\s*-->"), r"-->|\1|"),
    (re.compile(r"--\s*'([^']*?)'\s*-->"), r"-->|\1|"),
    (re.compile(r"-\.\s*\"([^\"]*?)\"\s*\.->"), r"-.|\1|.->"),
    (re.compile(r"-\.\s*'([^']*?)'\s*\.->"), r"-.|\1|.->"),
    (re.compile(r"==\s*\"([^\"]*?)\"\s*==>"), r"==>|\1|"),
    (re.compile(r"==\s*'([^']*?)'\s*==>"), r"==>|\1|"),
]

# Unquoted edge labels (space-delimited) -> pipe syntax
_EDGE_UNQUOTED_REPLACERS = [
    (re.compile(r"--\s+([^\"'|\n][^|\n]*?)\s+-->"), lambda m: f"-->|{m.group(1).strip()}|"),
    (re.compile(r"-\.\s+([^\"'|\n][^|\n]*?)\s+\.->"), lambda m: f"-.|{m.group(1).strip()}|.->"),
    (re.compile(r"==\s+([^\"'|\n][^|\n]*?)\s+==>"), lambda m: f"==>|{m.group(1).strip()}|"),
]

_DUP_ARROW_FIXES = [
    (re.compile(r"-->\|([^|]*?)\|\s*-->"), r"-->|\1|"),
    (re.compile(r"==>\|([^|]*?)\|\s*==>"), r"==>|\1|"),
]

_TRIM_PIPES_RE = re.compile(r"\|\s+([^|]*?)\s+\|")

_UNQUOTED_NODE_SQUARE = re.compile(r"\b([A-Za-z0-9_:-]+)\[(?![\"'])(?=[^\]\n]*[()：:])([^\]\n]*)\]")
_UNQUOTED_NODE_BRACE = re.compile(r"\b([A-Za-z0-9_:-]+)\{(?![\"'])(?=[^}\n]*[()：:])([^}\n]*)\}")

_SUBGRAPH_TITLE_LINE = re.compile(r"^(\s*subgraph\s+)([^\n]+)$", re.M)

_FENCE_ANY = re.compile(r"```(mermaid|mermai)[^\n]*\n([\s\S]*?)```", re.M)
_MISSPELLED_LANG = re.compile(r"```mermai\b")


def _sanitize_block(block: str) -> Tuple[str, bool]:
    changed = False
    out = _EOL_RE.sub("\n", block)
    if out != block:
        changed = True

    # 1) trailing semicolons
    new = _TRAILING_SEMI_RE.sub("", out)
    if new != out:
        changed = True
        out = new

    # 2) quoted edge labels -> pipes
    for pat, repl in _EDGE_QUOTED_REPLACERS:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new

    # 3) unquoted labels -> pipes
    for pat, repl in _EDGE_UNQUOTED_REPLACERS:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new

    # 4) duplicate arrows
    for pat, repl in _DUP_ARROW_FIXES:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new

    # 5) trim inside pipes
    new = _TRIM_PIPES_RE.sub(lambda m: f"|{m.group(1).strip()}|", out)
    if new != out:
        changed = True
        out = new

    # 6) quote node labels in [] / {}
    new = _UNQUOTED_NODE_SQUARE.sub(lambda m: f"{m.group(1)}[\"{m.group(2)}\"]", out)
    if new != out:
        changed = True
        out = new
    new = _UNQUOTED_NODE_BRACE.sub(lambda m: f"{m.group(1)}{{\"{m.group(2)}\"}}", out)
    if new != out:
        changed = True
        out = new

    # 7) subgraph titles
    def _fix_subgraph(m: re.Match) -> str:
        pre, name = m.group(1), (m.group(2) or "").strip()
        if not name:
            return m.group(0)
        if name.startswith('"') or name.startswith("'"):
            return m.group(0)
        if '[' in name:
            return m.group(0)
        if re.search(r"[()：:]", name):
            return f"{pre}\"{name}\""
        return m.group(0)

    new = _SUBGRAPH_TITLE_LINE.sub(_fix_subgraph, out)
    if new != out:
        changed = True
        out = new

    return out, changed


def sanitize_mermaid_in_markdown(md: str) -> Tuple[str, List[Dict[str, int]]]:
    if not md:
        return md, []
    content = _MISSPELLED_LANG.sub("```mermaid", md)

    parts: List[str] = []
    last = 0
    idx = 0
    issues: List[Dict[str, int]] = []
    for m in _FENCE_ANY.finditer(content):
        idx += 1
        parts.append(content[last:m.start()])
        inner = m.group(2)
        fixed, changed = _sanitize_block(inner)
        issues.append({"block_index": idx, "changed": 1 if changed else 0})
        parts.append("```mermaid\n" + fixed + "```")
        last = m.end()
    parts.append(content[last:])
    return ("".join(parts), issues)
