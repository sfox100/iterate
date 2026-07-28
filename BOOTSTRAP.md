# iterate - Bootstrap Instructions for Claude Code

This file contains everything Claude Code needs to set up an autonomous iteration loop
for improving a non-coding document. Give this file to Claude Code and tell it what
you're working on. It will create the entire system for you.

## How to use this file

1. Open Claude Code in a new, empty project directory
2. Say: "Read BOOTSTRAP.md and set up an iteration loop for me. I'm working on [describe your document]."
3. Claude Code will create all the files, customise the critic personas for your task, and explain how to run it.

Alternatively, paste the contents of this file into Claude Code directly.

---

## Instructions for Claude Code

You are setting up an autonomous document iteration loop based on the "iterate" technique
(autoresearch for text). The user will tell you what document they're working on. Your job
is to create a working iteration system customised to their specific task.

### Step 1: Ask the user what they're working on

Ask these questions (adapt based on what they've already told you):
- What document are you writing? (strategy, proposal, essay, blog post, spec, other?)
- Who is the audience? Who will read this?
- What's the goal? What should the reader think/do/feel after reading?
- Do you have any reference material or research to use as evidence? (If yes, ask them to put it in an evidence/ directory)
- Do you have an existing draft, or should we generate a seed from scratch?
- Any specific voice, tone, or style requirements?

### Step 2: Create the project structure

Create these files and directories:
```
./
  program.md        # The brief + critic personas (you write this based on user answers)
  evidence/         # Directory for reference material
  iterate.py        # The iteration engine (copy from below)
  requirements.txt  # Dependencies
```

### Step 3: Write program.md

Based on the user's answers, write a program.md with:

1. `## What You Are Producing` - specific brief based on their answers
2. `## Critics` - 3-4 named critic personas with `### critic_id: Display Name` format.

**How to design critics for any task:**
- One critic should be the **target reader/audience** - "Would you actually [buy this / share this / forward this / act on this]?"
- One critic should be the **internal skeptic** - "Why not do this differently? What's the obvious flaw?"
- One critic should be the **builder/implementer** - someone who has to act on whatever the document proposes
- One critic (optional) should be the **domain expert** who has seen everything in this space

Each critic persona should have:
- A specific name, role, and backstory (not just "an investor" but "a Series A investor who has seen 200+ startups this year")
- A specific agenda that conflicts with at least one other critic's agenda
- 2-3 specific questions they should answer
- Instruction to keep feedback to 4-6 sentences

3. `## Settings` - min_words, max_words, iterations (defaults: 800, 5000, 10)
4. `## Writer Instructions` - specific to the document type
5. `## What NOT to Do` - anti-patterns for this document type
6. `## Web Searches` - 3-6 search queries relevant to the topic (optional)

### Step 4: Write iterate.py

Create iterate.py with the following code. This is the complete iteration engine.

```python
#!/usr/bin/env python3
"""
iterate - autoresearch for text

An autonomous iteration loop for improving non-coding documents through
multi-persona critic feedback.

Usage:
    python iterate.py                          # Default: 10 iterations
    python iterate.py --max-iterations 20      # Run 20 iterations
    python iterate.py --seed-only              # Just generate the seed document
    python iterate.py --resume                 # Resume from existing document.md
    python iterate.py --cli                    # Use Claude CLI (free with Max plan)
"""

import anthropic
import json
import subprocess
import time
import re
import os
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(".")
EVIDENCE_DIR = BASE_DIR / "evidence"
DOCUMENT_FILE = BASE_DIR / "document.md"
PROGRAM_FILE = BASE_DIR / "program.md"
EXPERIMENTS_LOG = BASE_DIR / "experiments.jsonl"
RESEARCH_NOTES_FILE = BASE_DIR / "research_notes.md"
RUN_LOG_FILE = BASE_DIR / "run_log.md"
VERSIONS_DIR = BASE_DIR / "versions"


def parse_program(path):
    text = path.read_text()
    result = {
        "title": "", "brief": "", "critics": {},
        "settings": {"min_words": 800, "max_words": 5000, "iterations": 10},
        "writer_instructions": "", "what_not_to_do": "", "web_searches": [],
    }
    title_match = re.match(r'^# (.+)', text)
    if title_match:
        result["title"] = title_match.group(1).strip()
    sections = re.split(r'^## ', text, flags=re.MULTILINE)
    for section in sections:
        if not section.strip():
            continue
        header = section.split('\n')[0].strip().lower()
        body = '\n'.join(section.split('\n')[1:]).strip()
        if header.startswith("what you are producing"):
            result["brief"] = body
        elif header.startswith("critics"):
            for cs in re.split(r'^### ', body, flags=re.MULTILINE):
                if not cs.strip():
                    continue
                lines = cs.strip().split('\n')
                h = lines[0].strip()
                b = '\n'.join(lines[1:]).strip()
                cid = h.split(':')[0].strip().lower().replace(' ', '_') if ':' in h else h.lower().replace(' ', '_')
                result["critics"][cid] = b
        elif header.startswith("settings"):
            for line in body.split('\n'):
                line = line.strip().lstrip('- ')
                if ':' in line:
                    k, v = line.split(':', 1)
                    k, v = k.strip().lower().replace(' ', '_'), v.strip()
                    result["settings"][k] = int(v) if v.isdigit() else v
        elif header.startswith("writer instruction"):
            result["writer_instructions"] = body
        elif header.startswith("what not to do"):
            result["what_not_to_do"] = body
        elif header.startswith("web search"):
            result["web_searches"] = [l.strip().lstrip('- ') for l in body.split('\n') if l.strip() and not l.startswith('#')]
    return result


_evidence_cache = {}

def load_all_evidence():
    if not EVIDENCE_DIR.exists():
        return "(No evidence directory)"
    parts = []
    for f in sorted(EVIDENCE_DIR.glob("*.md")):
        c = f.read_text()
        _evidence_cache[f.name] = c
        parts.append(f"--- {f.name} ---\n{c}")
    return "\n\n".join(parts) or "(No evidence files)"


def evidence_search(query, max_results=15):
    terms = [t for t in query.lower().split() if len(t) > 2]
    if not _evidence_cache:
        load_all_evidence()
    results = []
    for path in sorted(EVIDENCE_DIR.glob("*.md")):
        if path.name not in _evidence_cache:
            _evidence_cache[path.name] = path.read_text()
        lines = _evidence_cache[path.name].split('\n')
        for i, line in enumerate(lines):
            matches = sum(1 for t in terms if t in line.lower())
            if matches >= max(1, len(terms) // 2):
                s, e = max(0, i-2), min(len(lines), i+3)
                results.append((matches, f"[{path.name}:{i+1}] " + '\n'.join(lines[s:e])))
    results.sort(key=lambda x: -x[0])
    return "\n\n".join(r[1] for r in results[:max_results]) or f"[No matches for '{query}']"


def web_search(query):
    import urllib.request
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return ""
    payload = json.dumps({
        "model": "sonar", "max_tokens": 800, "temperature": 0.1,
        "messages": [{"role": "system", "content": "Be precise and concise."}, {"role": "user", "content": query}],
        "web_search_options": {"search_context_size": "medium"},
    }).encode()
    req = urllib.request.Request("https://api.perplexity.ai/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                r = json.load(resp)
            content = r["choices"][0]["message"]["content"]
            cites = r.get("citations", [])
            return content + ("\nSources: " + ", ".join(cites[:3]) if cites else "")
        except Exception as e:
            if attempt == 0: time.sleep(2)
            else: return f"[Search error: {e}]"
    return ""


def run_web_searches(queries, label=""):
    if not os.environ.get("PERPLEXITY_API_KEY"):
        return ""
    results = []
    for q in queries:
        if label: log_live(f"    [{label}] web: {q[:60]}")
        r = web_search(q)
        if r: results.append(f"[web_search: {q}]\n{r}")
    return "\n\n---\n\n".join(results)


def call_claude_cli(prompt, timeout=600):
    for attempt in range(2):
        try:
            r = subprocess.run(["claude", "-p", "-", "--output-format", "text",
                "--disallowed-tools", "Write", "Edit", "Bash", "NotebookEdit"],
                input=prompt, capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0: return r.stdout
            if attempt == 0: time.sleep(5)
            else: raise RuntimeError(f"CLI failed: {r.stderr[:200]}")
        except subprocess.TimeoutExpired:
            if attempt == 0: log_live("  CLI timeout, retrying...")
            else: raise RuntimeError(f"CLI timed out after {timeout}s")
    return ""


def call_claude_api(client, prompt, model="claude-sonnet-4-20250514", max_tokens=8000):
    return client.messages.create(model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]).content[0].text


def call_claude(client, prompt, use_cli=False, model="claude-sonnet-4-20250514", max_tokens=8000, timeout=600):
    return call_claude_cli(prompt, timeout) if use_cli else call_claude_api(client, prompt, model, max_tokens)


def log_live(msg):
    print(msg)
    with open(RUN_LOG_FILE, "a") as f: f.write(msg + "\n")

def log_experiment(data):
    with open(EXPERIMENTS_LOG, "a") as f: f.write(json.dumps(data) + "\n")

def save_version(doc, version, kept):
    VERSIONS_DIR.mkdir(exist_ok=True)
    (VERSIONS_DIR / f"v{version:03d}_{'kept' if kept else 'rejected'}.md").write_text(doc)

def next_version_number():
    VERSIONS_DIR.mkdir(exist_ok=True)
    nums = [int(m.group(1)) for f in VERSIONS_DIR.glob("v*_*.md") if (m := re.match(r'v(\d+)_', f.name))]
    return max(nums) + 1 if nums else 0

def load_research_notes():
    return RESEARCH_NOTES_FILE.read_text() if RESEARCH_NOTES_FILE.exists() else ""

def append_research_notes(text):
    with open(RESEARCH_NOTES_FILE, "a") as f: f.write(f"\n---\n{datetime.now().strftime('%H:%M')} | {text}\n")


def run_single_critic(client, cid, prompt, doc, evidence, program, use_cli=False):
    search_results = ""
    if program.get("web_searches"):
        import random
        queries = random.Random(hash(cid)).sample(program["web_searches"], min(2, len(program["web_searches"])))
        search_results = run_web_searches(queries, label=cid)
    full = f"""{prompt}\n\n## Context\n{program.get('brief','')}\n\n## Evidence\n{evidence}\n{f'{chr(10)}## Research{chr(10)}{search_results}' if search_results else ''}\n\n## Document\n{doc}"""
    try:
        log_live(f"    [{cid}] generating feedback...")
        return (cid, call_claude(client, full, use_cli=use_cli, timeout=300).strip())
    except Exception as e:
        return (cid, f"Error: {e}")


def run_red_team(client, doc, evidence, program, critics, use_cli=False):
    results = {}
    with ThreadPoolExecutor(max_workers=min(len(critics), 5)) as pool:
        futures = [pool.submit(run_single_critic, client, cid, p, doc, evidence, program, use_cli) for cid, p in critics.items()]
        for f in as_completed(futures): n, fb = f.result(); results[n] = fb
    return results


def run_writer(client, doc, red_team, program, evidence, iteration, use_cli=False):
    rt_str = "\n".join(f"  [{n}]: {fb}" for n, fb in red_team.items())
    research = load_research_notes()[-3000:]
    search_results = ""
    if program.get("web_searches"):
        import random
        queries = random.Random(iteration).sample(program["web_searches"], min(3, len(program["web_searches"])))
        search_results = run_web_searches(queries, label="writer")
    wi = program.get("writer_instructions", "")
    wn = program.get("what_not_to_do", "")
    mn, mx = program["settings"].get("min_words", 800), program["settings"].get("max_words", 5000)
    prompt = f"""You are improving a document through iterative critic feedback.

## Brief\n{program.get('brief','')}\n\n## Evidence\n{evidence}\n{f'{chr(10)}## Research{chr(10)}{search_results}' if search_results else ''}
## Current Document (Iteration {iteration})\n{doc}\n\n## Critic Feedback\n{rt_str}
{f'{chr(10)}## Research Notes{chr(10)}{research}' if research else ''}
## Instructions
Pick the 2-3 STRONGEST objections. Address them surgically. Copy strong sections verbatim.
{f'{chr(10)}## Writer Instructions{chr(10)}{wi}' if wi else ''}{f'{chr(10)}## What NOT to Do{chr(10)}{wn}' if wn else ''}

Output: 2-3 sentences on what changed, then the COMPLETE document ({mn}-{mx} words).
If you learn something new: <research_note>what you learned</research_note>"""

    for attempt in range(2):
        if attempt > 0:
            log_live(f"  Writer retry...")
            prompt = f"Previous output too short. Output the COMPLETE document ({mn}-{mx} words).\n\n## Feedback\n{rt_str}\n\n## Current\n{doc}"
        else:
            log_live(f"  Writer generating...")
        response = call_claude(client, prompt, use_cli=use_cli, timeout=600)
        nm = re.search(r'<research_note>(.*?)</research_note>', response, re.DOTALL)
        if nm:
            append_research_notes(f"Iter {iteration}: {nm.group(1).strip()}")
            response = response[:nm.start()] + response[nm.end():]
        lines = response.strip().split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#'):
                d = '\n'.join(lines[i:])
                if len(d.split()) >= mn // 2:
                    return d, '\n'.join(lines[:i]).strip() or "update"
                break
    return response, "update"


def generate_seed(client, program, evidence, use_cli=False):
    search_results = ""
    if program.get("web_searches"):
        log_live("Seed: web searches...")
        search_results = run_web_searches(program["web_searches"][:3], label="seed")
    wi = program.get("writer_instructions", "")
    mn, mx = program["settings"].get("min_words", 800), program["settings"].get("max_words", 5000)
    prompt = f"""Write the initial draft of a document.\n\n## Brief\n{program.get('brief','')}\n\n## Evidence\n{evidence}\n{f'{chr(10)}## Research{chr(10)}{search_results}' if search_results else ''}\n{f'{chr(10)}## Instructions{chr(10)}{wi}' if wi else ''}
\nOutput: 2-3 sentences on approach, then COMPLETE document ({mn}-{mx} words)."""
    log_live("Generating seed...")
    response = call_claude(client, prompt, max_tokens=16000, use_cli=use_cli, timeout=900)
    nm = re.search(r'<research_note>(.*?)</research_note>', response, re.DOTALL)
    if nm:
        append_research_notes(f"Seed: {nm.group(1).strip()}")
        response = response[:nm.start()] + response[nm.end():]
    for i, line in enumerate(response.strip().split('\n')):
        if line.startswith('#'): return '\n'.join(response.strip().split('\n')[i:])
    return response


def main():
    parser = argparse.ArgumentParser(description="iterate - autoresearch for text")
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--cli", action="store_true", help="Use Claude CLI (free with Max plan)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv; load_dotenv()
    except ImportError:
        pass

    if not PROGRAM_FILE.exists():
        print("Error: program.md not found. Create one from a template or use BOOTSTRAP.md.")
        return

    program = parse_program(PROGRAM_FILE)
    critics = program["critics"]
    max_iter = args.max_iterations or program["settings"].get("iterations", 10)

    if not critics:
        print("Error: No critics in program.md. Add ### subsections under ## Critics.")
        return

    use_cli = args.cli
    client = None
    if not use_cli:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY not set. Set it or use --cli.")
            return
        client = anthropic.Anthropic()

    with open(RUN_LOG_FILE, "a") as f:
        f.write(f"\n# {datetime.now().strftime('%Y-%m-%d %H:%M')} | {'CLI' if use_cli else 'API'} | {len(critics)} critics\n\n")
    VERSIONS_DIR.mkdir(exist_ok=True)

    log_live(f"iterate - autoresearch for text | {'CLI' if use_cli else 'API'} | {len(critics)} critics | {max_iter} iterations")

    evidence = load_all_evidence()
    if EVIDENCE_DIR.exists():
        log_live(f"Evidence: {len(evidence):,} chars from {len(list(EVIDENCE_DIR.glob('*.md')))} files")

    if os.environ.get("PERPLEXITY_API_KEY"):
        log_live(f"Web search: enabled ({len(program.get('web_searches', []))} queries)")
    else:
        log_live("Web search: disabled (no PERPLEXITY_API_KEY)")

    start_v = next_version_number()
    if start_v > 0: log_live(f"Continuing from version {start_v}")

    rt = {}
    if args.resume and DOCUMENT_FILE.exists():
        log_live("Resuming from document.md")
        doc = DOCUMENT_FILE.read_text()
    elif DOCUMENT_FILE.exists() and not args.seed_only:
        log_live("Using existing document.md")
        doc = DOCUMENT_FILE.read_text()
    else:
        doc = generate_seed(client, program, evidence, use_cli)
        DOCUMENT_FILE.write_text(doc)
        log_live(f"Seed: {len(doc.split())} words")

    if args.seed_only:
        save_version(doc, start_v, True)
        log_live("Seed generated. Run without --seed-only to iterate.")
        return

    log_live(f"Initial red-team ({len(critics)} critics)...")
    rt = run_red_team(client, doc, evidence, program, critics, use_cli)
    for n, fb in rt.items(): log_live(f"  [{n}]: {fb[:150].replace(chr(10),' ')}...")
    save_version(doc, start_v, True)

    for i in range(1, max_iter + 1):
        vn = start_v + i
        try:
            log_live(f"\n{'='*60}\nIteration {i}/{max_iter} (v{vn:03d})\n{'='*60}")
            new_doc, desc = run_writer(client, doc, rt, program, evidence, vn, use_cli)
            log_live(f"  Writer: {desc[:120]}")
            log_live(f"  Red-teaming...")
            new_rt = run_red_team(client, new_doc, evidence, program, critics, use_cli)
            wc = len(new_doc.split())
            mn = program["settings"].get("min_words", 800)
            if wc < mn // 2:
                log_live(f"  SKIPPED - collapsed ({wc} words)")
                save_version(new_doc, vn, False)
            else:
                doc = new_doc
                DOCUMENT_FILE.write_text(doc)
                save_version(new_doc, vn, True)
            rt = new_rt
            for n, fb in new_rt.items(): log_live(f"    [{n}]: {fb[:150].replace(chr(10),' ')}...")
            log_experiment({"iteration": i, "version": vn, "timestamp": datetime.now().isoformat(),
                "description": desc[:200], "word_count": wc, "red_team": {k: v[:300] for k,v in new_rt.items()}})
        except KeyboardInterrupt:
            log_live(f"\nStopped after {i-1} iterations"); break
        except Exception as e:
            log_live(f"  Error: {e}"); import traceback; traceback.print_exc(); continue

    log_live(f"\n{'='*60}\nDONE - {i} iterations | {len(doc.split())} words | versions/{VERSIONS_DIR}")


if __name__ == "__main__":
    main()
```

### Step 5: Create requirements.txt

```
anthropic
python-dotenv
```

### Step 6: Help the user configure

After creating the files:
1. Confirm the program.md looks right for their task
2. Ask if they have evidence files to add
3. If they have an existing draft, save it as document.md
4. Explain how to run: `python iterate.py --max-iterations 10`
5. Explain: `--cli` flag uses Claude CLI (free with Max plan)
6. Explain: set `PERPLEXITY_API_KEY` for web search (optional)

### Step 7: Offer to run it

Ask if they want you to run the first iteration right now (via `python iterate.py --seed-only`
to generate the seed, or `python iterate.py --max-iterations 3` for a quick test run).

---

## Reference: TECHNIQUE.md

For the full explanation of the technique (7 design decisions, iteration curve,
critic design principles, cost estimates), see TECHNIQUE.md in the iterate repository:
https://github.com/sfox100/iterate
