# iterate

**autoresearch for text**

An autonomous iteration loop for improving non-coding documents - strategy memos, proposals, essays, blog posts - through multi-persona critic feedback.

Inspired by Karpathy's [autoresearch](https://github.com/karpathy/autoresearch). Instead of optimising `train.py` against validation loss, this optimises prose documents against named critic personas who each bring a structurally different agenda.

```
Writer (Claude) ──> 2-5 Critics (parallel) ──> Writer addresses strongest objections ──> repeat
```

10 iterations. 30-50 minutes. Every version saved.

---

## Two ways to start

### Option 1: Let Claude Code set it up (fastest)

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), give it [BOOTSTRAP.md](BOOTSTRAP.md) and tell it what you're working on. It will create everything customised to your specific task.

```
claude "Read BOOTSTRAP.md and set up an iteration loop. I'm working on a strategy memo for my startup's next product direction."
```

### Option 2: Manual setup (5 minutes)

```bash
git clone https://github.com/sfox100/iterate.git
cd iterate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

Pick a template and copy it:
```bash
cp templates/strategy.md program.md    # or proposal.md, blog-post.md, essay.md, product-spec.md
```

Edit `program.md` to describe your document and customise the critic personas.

Add reference material to `evidence/`:
```bash
mkdir -p evidence
# Add .md files with research, notes, data, transcripts, etc.
```

Run it:
```bash
python iterate.py --max-iterations 10
```

Watch it work. Read the output in `document.md` and the full progression in `versions/`.

---

## Why this works

Karpathy's autoresearch has `val_bpb` - a single number that tells you if the model improved. Prose doesn't have that. You can't score a strategy document on a 0-1 scale and have it mean anything useful.

The substitute is **named critic personas with conflicting agendas**. Each critic tries to find the fatal flaw from their perspective:

- The **investor** asks: "Is this a $100M outcome? Would I fund this?"
- The **customer** asks: "What sounds like every other vendor pitch I've heard?"
- The **CTO** asks: "Can we actually build this with our team and timeline?"
- The **sales advisor** asks: "Who has a burning project THIS QUARTER that needs this?"

These critics can't all be satisfied at once. The investor wants ambition; the CTO wants realism. The customer wants proof; the sales advisor wants urgency. This tension forces the writer to make real choices rather than producing bland compromise text.

### The iteration curve

A consistent pattern across different types of content:

- **Phase 1 (iterations 1-2):** Fix what's WRONG - structural problems, jargon, misaligned framing. Biggest single improvement.
- **Phase 2 (iterations 3-5):** Find what's MISSING - gaps, absent evidence, missing scenarios.
- **Phase 3 (iterations 6-8):** Handle the SKEPTIC - intellectual honesty, counterarguments, edge cases.
- **Phase 4+ (8+):** Diminishing returns. The ceiling is real-world data - the document can't improve further without actual user feedback or deployment results.

8-10 iterations is the sweet spot. Going beyond that is fine if running overnight, but don't expect phase 3+ gains to match phases 1-2.

### Key design decisions

These emerged from running 50+ critic personas across 30+ iteration rounds. Each represents a wrong approach tried first:

1. **No quality scoring gate.** Numeric scores measure text properties, not document quality. A critic asking "would I actually invest?" tests strategic quality. Feedback-only with a length gate (reject if the document collapsed) works better.

2. **Surgical improvements, not full rewrites.** "Copy sections that are already strong verbatim. Fix the 2-3 weakest areas." Full rewrites regress dimensions that were already working.

3. **Writer picks which critics to address.** Addressing all 5 critics at once produces shallow responses. Picking the 2-3 strongest objections produces deep improvements. The rest get addressed in later rounds.

4. **Curated evidence, not raw dumps.** 500KB of raw transcripts produces thin output. 100-300KB of condensed summaries produces focused, evidence-grounded writing.

5. **Named personas, not generic roles.** "A Series A investor who has seen 200+ startups this year" generates structurally different feedback than "an investor."

6. **Critics must have conflicting agendas.** If your critics agree, you effectively have one critic. The value is productive disagreement.

7. **Pre-executed web searches.** Run searches in Python before the API call and inject results. More reliable than model tool-use in stateless CLI calls.

Read [TECHNIQUE.md](TECHNIQUE.md) for the full writeup with detailed examples and cost analysis.

---

## Templates

| Template | Critics | Best for |
|----------|---------|----------|
| [strategy.md](templates/strategy.md) | Investor, Customer, CTO, Sales advisor | Business strategy, product direction |
| [proposal.md](templates/proposal.md) | Decision-maker, Skeptic, Technical reviewer, Budget holder | Client proposals, SOWs |
| [blog-post.md](templates/blog-post.md) | Target reader, Editor, Contrarian | Long-form content, thought leadership |
| [essay.md](templates/essay.md) | Generous reader, Academic, Practitioner | Essays, research pieces |
| [product-spec.md](templates/product-spec.md) | End user, Engineer, PM, Support | Product specs, feature briefs |

Each template includes pre-configured critic personas designed to create productive tension. Customise them for your specific situation.

---

## CLI options

```
python iterate.py                          # Run with defaults from program.md
python iterate.py --max-iterations 20      # Override iteration count
python iterate.py --seed-only              # Generate seed document only
python iterate.py --resume                 # Resume from existing document.md
python iterate.py --cli                    # Use Claude CLI (free with Max plan)
python iterate.py --web-search             # Enable Perplexity web search (needs PERPLEXITY_API_KEY)
python iterate.py --model claude-opus-4-20250514  # Use a different model
```

---

## Requirements

- Python 3.10+
- An Anthropic API key (`ANTHROPIC_API_KEY`), OR Claude Code with a Max plan (`--cli` flag)
- Optional: `--web-search` flag + Perplexity API key (`PERPLEXITY_API_KEY`) for live web research

---

## How it compares

| | iterate | autoresearch | Adversary Loops |
|---|---|---|---|
| Domain | Prose/strategy | ML code | Prose (single critic) |
| Quality signal | Named critic feedback | val_bpb (numeric) | Anonymous critique |
| Critics | 2-5 named personas | N/A | 1 anonymous |
| Evidence base | Yes | Train data | No |
| Parallel critics | Yes | N/A | No |
| Web search | Optional | No | No |
| Open source | Yes | Yes | No |

---

## Cost

**Using the API** (Claude Sonnet): ~$1.50-3.00 for 10 iterations with 4 critics.

**Using Claude CLI** (`--cli` flag, requires Max plan): Free for Claude calls. Add ~$0.30 for Perplexity if using `--web-search`.

---

## Project structure

After running, your directory will look like:

```
./
  program.md           # Your brief and critic personas
  document.md          # The current best version
  evidence/            # Your reference material
  versions/            # Every version (v000_kept.md, v001_kept.md, ...)
  run_log.md           # Human-readable log
  experiments.jsonl    # Machine-readable experiment data
  research_notes.md    # Accumulated findings (if web search enabled)
```

---

## License

MIT
