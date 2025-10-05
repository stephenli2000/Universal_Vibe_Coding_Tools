# Universal Vibe Coding Tools — Chat‑Only Vibe

Keep it simple. No IDE plugins, no lock‑in. These tiny scripts package the **right** text so you can drop a single file into a coding chat AI and get on the same page fast, with minimal back‑and‑forth.

---

## Philosophy
- **Chat‑only workflow:** You + AI in one thread; everything needed is pasted or attached as a single text bundle.
- **Vibe coding:** simple logs, human‑like pace, pragmatic output; optimize for clarity over ceremony.
- **Minimum sync cost:** package sources or relevant diffs so AI can reason over the exact context you see.

---

## Quick Start
```bash
python3 -m venv venv && source venv/bin/activate
# run any tool with: python3 <tool>.py [args]
```
1) Run a tool below to generate a **single text file**.
2) Attach or paste that file into your coding chat.
3) Prompt the AI with what you want (review, refactor, tests, bug fix).

> Tip: Remove secrets before packaging; add the output filename to `.gitignore`.

---

## Tools

### 1) `concatenate_text_files.py` — Snapshot all text files in a repo
**What:** Recursively collects text‑like files (e.g., `.py`, `.md`, `.json`, etc.), skips noisy folders (`.git/`, `node_modules/`, `dist/`, etc.), and writes one bundle with headers per file.

**Why:** Share the **whole project context** in chat without zipping.

**Use it**
```bash
python3 concatenate_text_files.py path/to/project
# → creates ./<project>.txt containing all included files with headers
```

---

### 2) `concatenate_python_files.py` — Bundle a script plus its local imports
**What:** Traces local Python imports starting from one or more entry scripts and concatenates those files into a single text artifact.

**Why:** Give AI the **exact Python dependency closure** it needs for reasoning, without external packages.

**Use it**
```bash
python3 concatenate_python_files.py project_root/ path/to/main.py [another.py ...]
# → writes project_root_concatenated.txt
```

---

### 3) `save_commits.py` — Package the changed files for a commit or range
**What:** Finds files changed in one commit (or between two commits) and writes their contents to a single text file with commit headers.

**Why:** Share **focused diffs** for targeted reviews or debugging.

**Use it**
```bash
# Single commit
python3 save_commits.py --this f9e8d7c

# Range (base..this)
python3 save_commits.py --base a1b2c3d --this f9e8d7c
# → writes <this>.txt or base-this.txt
```

---

### 4) `analyze_folder.py` — Quick repo inventory
**What:** Scans a directory, groups by file type, totals sizes, and shows a small table (count, total size, example largest file). No bundle output—just fast insight.

**Why:** Decide **what to package** (and what to ignore) before chatting.

**Use it**
```bash
python3 analyze_folder.py              # analyze current folder
python3 analyze_folder.py path/to/dir  # analyze a specific directory
```

---

## Chat‑Only Workflow Examples

**A) Whole‑project review**
1. `concatenate_text_files.py ./myapp` → `myapp.txt`
2. Attach `myapp.txt` in chat.
3. Ask: “Review for structure, add tests for X, and propose a minimal refactor.”

**B) Python bug fix in a small tool**
1. `concatenate_python_files.py ./tools ./tools/runner.py` → `tools_concatenated.txt`
2. Attach; ask: “There’s a crash when input is empty. Fix and add doctests.”

**C) Focused PR feedback**
1. `save_commits.py --base abc123 --this def456` → `abc123-def456.txt`
2. Attach; ask: “Explain risk, edge cases, and missing tests in this change.”

---

## Best Practices
- **Keep bundles small:** exclude vendor/large assets; your chat will run faster and be more accurate.
- **One truthy file:** Prefer a single, clearly‑labeled artifact per conversation.
- **Scrub secrets:** `.env`, keys, tokens—drop or redact before packaging.
- **Name clearly:** `<project>_snapshot.txt`, `<root>_concatenated.txt`, `base-this.txt`.

---

## FAQ
**Why text instead of zip?** Text is immediately visible/searchable in chat, avoids unzip friction, and keeps you and AI tightly in sync.

**Does this include third‑party deps?** No—these tools focus on your source and local imports. Mention external packages in your prompt or attach `requirements.txt`.

---

## License & Contributions
Use at your own risk; PRs welcome. Keep changes tiny, logs clear, and defaults sensible.

