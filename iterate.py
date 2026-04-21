#!/usr/bin/env python3
"""
iterate - autoresearch for text

An autonomous iteration loop for improving non-coding documents (strategy,
proposals, essays, content) through multi-persona critic feedback.

Inspired by Karpathy's autoresearch. Instead of optimising train.py against
val_bpb, this optimises a prose document against named critic personas who
each bring a structurally different agenda.

Usage:
    python iterate.py                          # Default: 10 iterations
    python iterate.py --max-iterations 20      # Run 20 iterations
    python iterate.py --seed-only              # Just generate the seed document
    python iterate.py --resume                 # Resume from existing document.md
    python iterate.py --cli                    # Use Claude CLI (free with Max plan)
    python iterate.py --web-search             # Enable Perplexity web search

Setup:
    pip install anthropic python-dotenv
    export ANTHROPIC_API_KEY=your_key
    # Optional: export PERPLEXITY_API_KEY=your_key (for web search)

Project structure:
    program.md      # Your brief: what to optimise, critic personas, settings
    evidence/       # Context files the writer and critics can reference
    document.md     # The document being iterated (created by seed if absent)
    versions/       # Every version saved (v000_kept.md, v001_kept.md, ...)
    run_log.md      # Human-readable log of what happened
    experiments.jsonl  # Machine-readable experiment log
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

# --- Paths ---------------------------------------------------------------

BASE_DIR = Path(".")
EVIDENCE_DIR = BASE_DIR / "evidence"
DOCUMENT_FILE = BASE_DIR / "document.md"
PROGRAM_FILE = BASE_DIR / "program.md"
EXPERIMENTS_LOG = BASE_DIR / "experiments.jsonl"
RESEARCH_NOTES_FILE = BASE_DIR / "research_notes.md"
RUN_LOG_FILE = BASE_DIR / "run_log.md"
VERSIONS_DIR = BASE_DIR / "versions"


# --- Parse program.md ----------------------------------------------------

def parse_program(path: Path) -> dict:
    """Parse program.md into structured config.

    Expected format:
        # Title
        ## What You Are Producing
        [free text brief]
        ## Critics
        ### critic_id: Display Name
        [persona prompt]
        ### another_id: Another Name
        [persona prompt]
        ## Settings
        - min_words: 800
        - max_words: 5000
        - iterations: 10
        ## Writer Instructions
        [mutation guidance]
        ## What NOT to Do
        [anti-patterns]
        ## Web Searches
        [optional: search queries for the writer, one per line]
    """
    text = path.read_text()
    result = {
        "title": "",
        "brief": "",
        "critics": {},
        "settings": {"min_words": 800, "max_words": 5000, "iterations": 10},
        "writer_instructions": "",
        "what_not_to_do": "",
        "web_searches": [],
    }

    # Split into sections by ## headers
    sections = re.split(r'^## ', text, flags=re.MULTILINE)

    # Title from first # header
    title_match = re.match(r'^# (.+)', text)
    if title_match:
        result["title"] = title_match.group(1).strip()

    for section in sections:
        if not section.strip():
            continue

        header_line = section.split('\n')[0].strip()
        body = '\n'.join(section.split('\n')[1:]).strip()
        header_lower = header_line.lower()

        if header_lower.startswith("what you are producing"):
            result["brief"] = body

        elif header_lower.startswith("critics"):
            # Parse ### subsections for individual critics
            critic_sections = re.split(r'^### ', body, flags=re.MULTILINE)
            for cs in critic_sections:
                if not cs.strip():
                    continue
                cs_lines = cs.strip().split('\n')
                cs_header = cs_lines[0].strip()
                cs_body = '\n'.join(cs_lines[1:]).strip()
                # Parse "critic_id: Display Name" or just "Display Name"
                if ':' in cs_header:
                    critic_id, display_name = cs_header.split(':', 1)
                    critic_id = critic_id.strip().lower().replace(' ', '_')
                else:
                    critic_id = cs_header.strip().lower().replace(' ', '_')
                result["critics"][critic_id] = cs_body

        elif header_lower.startswith("settings"):
            for line in body.split('\n'):
                line = line.strip().lstrip('- ')
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    val = val.strip()
                    if val.isdigit():
                        val = int(val)
                    result["settings"][key] = val

        elif header_lower.startswith("writer instruction"):
            result["writer_instructions"] = body

        elif header_lower.startswith("what not to do"):
            result["what_not_to_do"] = body

        elif header_lower.startswith("web search"):
            result["web_searches"] = [
                line.strip().lstrip('- ')
                for line in body.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]

    if not result["critics"]:
        print("WARNING: No critics found in program.md. Check the ## Critics section.")
        print("Each critic should be a ### subsection under ## Critics.")

    return result


# --- Evidence -------------------------------------------------------------

_evidence_cache: dict[str, str] = {}


def load_all_evidence() -> str:
    """Load all .md files from the evidence directory."""
    if not EVIDENCE_DIR.exists():
        return "(No evidence directory found)"
    all_files = sorted(f.name for f in EVIDENCE_DIR.glob("*.md"))
    if not all_files:
        return "(No evidence files found)"
    parts = []
    for fname in all_files:
        path = EVIDENCE_DIR / fname
        content = path.read_text()
        _evidence_cache[fname] = content
        parts.append(f"--- {fname} ---\n{content}")
    return "\n\n".join(parts)


def evidence_search(query: str, max_results: int = 15) -> str:
    """Simple keyword search across evidence files."""
    query_lower = query.lower()
    terms = [t for t in query_lower.split() if len(t) > 2]
    if not terms:
        return f"[No valid search terms in '{query}']"

    # Ensure evidence is loaded
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
                start, end = max(0, i - 2), min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                results.append((matches, f"[{path.name}:{i+1}] {context}"))
    results.sort(key=lambda x: -x[0])
    return "\n\n".join(r[1] for r in results[:max_results]) or f"[No matches for '{query}']"


# --- Web search (Perplexity, optional) ------------------------------------

def web_search(query: str) -> str:
    """Search the web via Perplexity API. Returns empty string if no API key."""
    import urllib.request
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return ""
    payload = json.dumps({
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be precise, factual, and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": 800,
        "temperature": 0.1,
        "web_search_options": {"search_context_size": "medium"},
    }).encode()
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.load(resp)
            content = result["choices"][0]["message"]["content"]
            citations = result.get("citations", [])
            if citations:
                content += "\nSources: " + ", ".join(citations[:3])
            return content
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                return f"[Search error: {e}]"
    return ""


def run_web_searches(queries: list[str], label: str = "") -> str:
    """Run multiple web searches, return formatted results. Skips if no API key."""
    if not os.environ.get("PERPLEXITY_API_KEY"):
        return ""
    results = []
    for q in queries:
        if label:
            log_live(f"    [{label}] web: {q[:60]}")
        r = web_search(q)
        if r:
            results.append(f"[web_search: {q}]\n{r}")
    return "\n\n---\n\n".join(results) if results else ""


# --- Claude invocation ----------------------------------------------------

def call_claude_cli(prompt: str, timeout: int = 600) -> str:
    """Call Claude via the CLI (free with Max plan)."""
    for attempt in range(2):
        try:
            result = subprocess.run(
                ["claude", "-p", "-", "--output-format", "text",
                 "--disallowed-tools", "Write", "Edit", "Bash", "NotebookEdit"],
                input=prompt, capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode == 0:
                return result.stdout
            if attempt == 0:
                log_live(f"  CLI retry in 5s...")
                time.sleep(5)
            else:
                raise RuntimeError(f"CLI failed: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            if attempt == 0:
                log_live(f"  CLI timeout, retrying...")
            else:
                raise RuntimeError(f"CLI timed out after {timeout}s")
    return ""


def call_claude_api(client: anthropic.Anthropic, prompt: str,
                    model: str = "claude-sonnet-4-20250514",
                    max_tokens: int = 8000) -> str:
    """Call Claude via the Anthropic API."""
    return client.messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    ).content[0].text


def call_claude(client, prompt, use_cli=False, model="claude-sonnet-4-20250514",
                max_tokens=8000, timeout=600):
    """Unified Claude caller. Uses CLI or API based on flag."""
    if use_cli:
        return call_claude_cli(prompt, timeout)
    return call_claude_api(client, prompt, model, max_tokens)


# --- Logging ---------------------------------------------------------------

def log_live(msg: str):
    """Print and append to run log."""
    print(msg)
    with open(RUN_LOG_FILE, "a") as f:
        f.write(msg + "\n")


def log_experiment(data: dict):
    """Append structured data to experiments log."""
    with open(EXPERIMENTS_LOG, "a") as f:
        f.write(json.dumps(data) + "\n")


def save_version(document: str, version: int, kept: bool):
    """Save a version of the document."""
    VERSIONS_DIR.mkdir(exist_ok=True)
    tag = "kept" if kept else "rejected"
    (VERSIONS_DIR / f"v{version:03d}_{tag}.md").write_text(document)


def next_version_number() -> int:
    """Find the next version number from existing version files."""
    VERSIONS_DIR.mkdir(exist_ok=True)
    existing = list(VERSIONS_DIR.glob("v*_*.md"))
    if not existing:
        return 0
    nums = []
    for f in existing:
        m = re.match(r'v(\d+)_', f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 0


def load_research_notes() -> str:
    """Load accumulated research notes from previous iterations."""
    return RESEARCH_NOTES_FILE.read_text() if RESEARCH_NOTES_FILE.exists() else ""


def append_research_notes(text: str):
    """Append a research note with timestamp."""
    with open(RESEARCH_NOTES_FILE, "a") as f:
        f.write(f"\n---\n{datetime.now().strftime('%H:%M')} | {text}\n")


# --- Red-team critics ------------------------------------------------------

def run_single_critic(client, critic_id: str, critic_prompt: str,
                      document: str, evidence: str, program: dict,
                      use_cli: bool = False) -> tuple[str, str]:
    """Run a single critic with evidence context."""
    # Build web search results if searches are configured
    search_results = ""
    if program.get("web_searches"):
        # Each critic gets 1-2 rotated searches from the pool
        import random
        rng = random.Random(hash(critic_id))
        queries = rng.sample(program["web_searches"],
                             min(2, len(program["web_searches"])))
        search_results = run_web_searches(queries, label=critic_id)

    full_prompt = f"""{critic_prompt}

## Context: What This Document Is
{program.get('brief', '')}

## Evidence Base
{evidence}

{f"## Fresh Research{chr(10)}{search_results}" if search_results else ""}

## Document to Review
{document}
"""
    try:
        log_live(f"    [{critic_id}] generating feedback...")
        response = call_claude(client, full_prompt, use_cli=use_cli, timeout=300)
        return (critic_id, response.strip())
    except Exception as e:
        return (critic_id, f"Error: {e}")


def run_red_team(client, document: str, evidence: str, program: dict,
                 critics: dict, use_cli: bool = False) -> dict[str, str]:
    """Run all critics in parallel."""
    results = {}
    max_workers = min(len(critics), 5)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(run_single_critic, client, cid, prompt,
                        document, evidence, program, use_cli)
            for cid, prompt in critics.items()
        ]
        for f in as_completed(futures):
            name, feedback = f.result()
            results[name] = feedback
    return results


# --- Writer agent -----------------------------------------------------------

def run_writer(client, document: str, red_team: dict, program: dict,
               evidence: str, iteration: int,
               use_cli: bool = False) -> tuple[str, str]:
    """Writer agent improves the document based on critic feedback."""
    redteam_str = "\n".join(
        f"  [{name}]: {fb}" for name, fb in red_team.items()
    )
    research = load_research_notes()
    research_trimmed = research[-3000:] if len(research) > 3000 else research

    # Run web searches for the writer
    search_results = ""
    if program.get("web_searches"):
        import random
        rng = random.Random(iteration)
        queries = rng.sample(program["web_searches"],
                             min(3, len(program["web_searches"])))
        log_live(f"  Writer researching...")
        search_results = run_web_searches(queries, label="writer")

    writer_instructions = program.get("writer_instructions", "")
    what_not_to_do = program.get("what_not_to_do", "")
    min_words = program["settings"].get("min_words", 800)
    max_words = program["settings"].get("max_words", 5000)

    prompt = f"""You are improving a document through an iterative feedback loop.

## What This Document Is
{program.get('brief', '')}

## Evidence Base
{evidence}

{f"## Fresh Web Research{chr(10)}{search_results}" if search_results else ""}

## Current Document (Iteration {iteration})
{document}

## Critic Feedback
{redteam_str}

## Research Notes (accumulated from previous iterations)
{research_trimmed if research_trimmed else "(none yet)"}

## How to Improve
Read the critics' feedback carefully. Each critic has a different agenda and
perspective. Pick the 2-3 STRONGEST objections and address them surgically.

Do NOT rewrite the entire document. Copy sections that are already strong
verbatim. Only modify the parts that need improvement.

{f"## Additional Writer Instructions{chr(10)}{writer_instructions}" if writer_instructions else ""}

{f"## What NOT to Do{chr(10)}{what_not_to_do}" if what_not_to_do else ""}

## Output Format
- First: 2-3 sentences describing what you changed and why (which critics you addressed)
- Then: the COMPLETE document with improvements applied
- The document must be {min_words}-{max_words} words
- Do NOT output only a summary of changes - output the full document

If you found useful new information, end with: <research_note>what you learned</research_note>

IMPORTANT: Your response MUST contain the complete document text. If it doesn't
include the full document, it will be rejected.
"""

    for attempt in range(2):
        if attempt > 0:
            log_live(f"  Writer retry (attempt {attempt + 1})...")
            retry_prompt = f"""Your previous output was too short. You MUST output the COMPLETE document.

## Changes to make based on critic feedback
{redteam_str}

## Current Document
{document}

## Instructions
Output the COMPLETE improved document ({min_words}-{max_words} words).
Start with 2-3 sentences about what you changed, then the full document.
"""
            response = call_claude(client, retry_prompt, use_cli=use_cli, timeout=600)
        else:
            log_live(f"  Writer generating...")
            response = call_claude(client, prompt, use_cli=use_cli, timeout=600)

        # Extract research notes
        note_match = re.search(r'<research_note>(.*?)</research_note>',
                               response, re.DOTALL)
        if note_match:
            append_research_notes(f"Iter {iteration}: {note_match.group(1).strip()}")
            response = response[:note_match.start()] + response[note_match.end():]

        # Extract description + document
        lines = response.strip().split('\n')
        for i, line in enumerate(lines):
            if line.startswith('#'):
                doc = '\n'.join(lines[i:])
                if len(doc.split()) >= min_words // 2:  # Allow some slack
                    desc = '\n'.join(lines[:i]).strip() or "document update"
                    return doc, desc
                else:
                    log_live(f"  Output too short ({len(doc.split())} words)")
                    break

    return response, "document update"


# --- Seed generation --------------------------------------------------------

def generate_seed(client, program: dict, evidence: str,
                  use_cli: bool = False) -> str:
    """Generate the initial document from the program brief and evidence."""
    search_results = ""
    if program.get("web_searches"):
        log_live("Seed: running web searches...")
        queries = program["web_searches"][:3]
        search_results = run_web_searches(queries, label="seed")

    writer_instructions = program.get("writer_instructions", "")
    min_words = program["settings"].get("min_words", 800)
    max_words = program["settings"].get("max_words", 5000)

    prompt = f"""You are writing the initial draft of a document.

## What to Produce
{program.get('brief', '')}

## Evidence Base
{evidence}

{f"## Fresh Web Research{chr(10)}{search_results}" if search_results else ""}

{f"## Writing Instructions{chr(10)}{writer_instructions}" if writer_instructions else ""}

## Output
- First: 2-3 sentences describing your approach
- Then: the COMPLETE document ({min_words}-{max_words} words)

Write a strong first draft. It will be improved through multiple rounds of
critic feedback, so don't try to be perfect - aim for solid structure and
clear arguments that can be refined.
"""

    log_live("Generating seed document...")
    response = call_claude(client, prompt, max_tokens=16000,
                           use_cli=use_cli, timeout=900)

    # Extract research notes
    note_match = re.search(r'<research_note>(.*?)</research_note>',
                           response, re.DOTALL)
    if note_match:
        append_research_notes(f"Seed: {note_match.group(1).strip()}")
        response = response[:note_match.start()] + response[note_match.end():]

    # Extract just the document (skip description lines)
    lines = response.strip().split('\n')
    for i, line in enumerate(lines):
        if line.startswith('#'):
            return '\n'.join(lines[i:])

    return response


# --- Main loop --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="iterate - autoresearch for text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python iterate.py                     # Run 10 iterations (default)
  python iterate.py --max-iterations 20 # Run 20 iterations
  python iterate.py --seed-only         # Generate seed document only
  python iterate.py --resume            # Resume from existing document
  python iterate.py --cli               # Use Claude CLI (free with Max plan)
  python iterate.py --model claude-opus-4-20250514  # Use a specific model
        """
    )
    parser.add_argument("--max-iterations", type=int, default=None,
                        help="Number of iterations (default: from program.md)")
    parser.add_argument("--seed-only", action="store_true",
                        help="Only generate the seed document")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing document.md")
    parser.add_argument("--cli", action="store_true",
                        help="Use Claude CLI instead of API (free with Max plan)")
    parser.add_argument("--web-search", action="store_true",
                        help="Enable Perplexity web search (requires PERPLEXITY_API_KEY)")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514",
                        help="Anthropic model to use (default: claude-sonnet-4-20250514)")
    args = parser.parse_args()

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional

    # Check program.md exists
    if not PROGRAM_FILE.exists():
        print("Error: program.md not found in current directory.")
        print("Create one from a template, or run: python iterate.py --help")
        return

    # Parse program
    program = parse_program(PROGRAM_FILE)
    critics = program["critics"]
    max_iterations = args.max_iterations or program["settings"].get("iterations", 10)

    # Web search is opt-in: only enable if --web-search flag is set AND key exists
    if not args.web_search:
        program["web_searches"] = []

    if not critics:
        print("Error: No critics found in program.md.")
        print("Add critic personas under ## Critics as ### subsections.")
        return

    # Set up Claude client
    use_cli = args.cli
    client = None
    if not use_cli:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set.")
            print("Either set the env var or use --cli for Claude CLI (Max plan).")
            return
        client = anthropic.Anthropic()

    # Init logging
    with open(RUN_LOG_FILE, "a") as f:
        f.write(f"\n# Run started {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                f"{'CLI' if use_cli else 'API'} | {len(critics)} critics\n\n")
    VERSIONS_DIR.mkdir(exist_ok=True)

    log_live(f"iterate - autoresearch for text")
    log_live(f"Mode: {'Claude CLI (Max plan)' if use_cli else f'API ({args.model})'}")
    log_live(f"Critics: {', '.join(critics.keys())}")
    log_live(f"Iterations: {max_iterations}")

    # Load evidence
    log_live("Loading evidence...")
    evidence = load_all_evidence()
    if EVIDENCE_DIR.exists():
        file_count = len(list(EVIDENCE_DIR.glob('*.md')))
        log_live(f"Evidence: {len(evidence):,} chars from {file_count} files")
    else:
        log_live("No evidence directory found (continuing without evidence)")

    # Web search status
    if args.web_search:
        if os.environ.get("PERPLEXITY_API_KEY"):
            log_live(f"Web search: enabled ({len(program.get('web_searches', []))} queries)")
        else:
            log_live("Web search: --web-search flag set but no PERPLEXITY_API_KEY found")
            program["web_searches"] = []
    else:
        log_live("Web search: off (use --web-search to enable)")

    # Determine starting version
    start_version = next_version_number()
    if start_version > 0:
        log_live(f"Continuing from version {start_version}")

    # Seed or resume
    red_team_feedback = {}
    if args.resume and DOCUMENT_FILE.exists():
        log_live("Resuming from existing document.md")
        document = DOCUMENT_FILE.read_text()
    elif DOCUMENT_FILE.exists() and not args.seed_only:
        log_live("Using existing document.md")
        document = DOCUMENT_FILE.read_text()
    else:
        document = generate_seed(client, program, evidence, use_cli)
        DOCUMENT_FILE.write_text(document)
        log_live(f"Seed: {len(document):,} chars, {len(document.split())} words")

    if args.seed_only:
        save_version(document, start_version, True)
        log_live("Seed generated. Run without --seed-only to iterate.")
        return

    # Initial red-team
    log_live(f"Initial red-team ({len(critics)} critics)...")
    red_team_feedback = run_red_team(client, document, evidence, program,
                                     critics, use_cli)
    for name, fb in red_team_feedback.items():
        log_live(f"  [{name}]: {fb[:150].replace(chr(10), ' ')}...")
    save_version(document, start_version, True)

    # Main loop
    for i in range(1, max_iterations + 1):
        version_num = start_version + i
        try:
            log_live(f"\n{'='*60}")
            log_live(f"Iteration {i}/{max_iterations} (version {version_num})")
            log_live(f"{'='*60}")

            # Writer improves based on feedback
            new_document, description = run_writer(
                client, document, red_team_feedback, program,
                evidence, version_num, use_cli,
            )
            log_live(f"  Writer: {description[:120]}")

            # Red-team the new version
            log_live(f"  Red-teaming ({len(critics)} critics)...")
            new_red_team = run_red_team(client, new_document, evidence,
                                        program, critics, use_cli)

            # Length gate: reject if document collapsed
            min_words = program["settings"].get("min_words", 800)
            word_count = len(new_document.split())
            if word_count < min_words // 2:
                log_live(f"  SKIPPED - collapsed ({word_count} words), keeping previous")
                save_version(new_document, version_num, False)
            else:
                max_words = program["settings"].get("max_words", 5000)
                if word_count > max_words * 1.2:
                    log_live(f"  WARNING: {word_count} words (target {min_words}-{max_words})")
                document = new_document
                DOCUMENT_FILE.write_text(document)
                save_version(new_document, version_num, True)

            red_team_feedback = new_red_team

            # Log feedback
            for name, fb in new_red_team.items():
                log_live(f"    [{name}]: {fb[:150].replace(chr(10), ' ')}...")

            # Structured log
            log_experiment({
                "iteration": i, "version": version_num,
                "timestamp": datetime.now().isoformat(),
                "description": description[:200],
                "word_count": word_count,
                "red_team": {k: v[:300] for k, v in new_red_team.items()},
            })

        except KeyboardInterrupt:
            log_live(f"\nStopped after {i - 1} iterations")
            break
        except Exception as e:
            log_live(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary
    log_live(f"\n{'='*60}")
    log_live(f"DONE - {i} iterations (versions {start_version}-{version_num})")
    log_live(f"Document: {DOCUMENT_FILE} ({len(document.split())} words)")
    log_live(f"All versions: {VERSIONS_DIR}/")


if __name__ == "__main__":
    main()
