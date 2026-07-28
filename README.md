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

## How it works

1. **program.md** defines what you're optimising for - the brief, audience, and 2-5 named critic personas
2. **evidence/** contains curated context files (research, notes, data)
3. The **writer** (Claude) generates or improves the document
4. **Critics** (Claude, in parallel) each evaluate from their specific perspective
5. The writer picks the 2-3 strongest objections and addresses them surgically
6. Every version is saved. Length gate rejects collapsed documents. Repeat.

Read [TECHNIQUE.md](TECHNIQUE.md) for the full explanation - 7 design decisions, the iteration curve, how to write good critics, cost estimates.

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
python iterate.py --model claude-opus-4-20250514  # Use a different model
```

---

## Requirements

- Python 3.10+
- An Anthropic API key (`ANTHROPIC_API_KEY`), OR Claude Code with a Max plan (`--cli` flag)
- Optional: Perplexity API key (`PERPLEXITY_API_KEY`) for web search

---

## How it compares

| | iterate | autoresearch | Adversary Loops |
|---|---|---|---|
| Domain | Prose/strategy | ML code | Prose (single critic) |
| Quality signal | Named critic feedback | val_bpb (numeric) | Anonymous critique |
| Critics | 2-5 named personas | N/A | 1 anonymous |
| Evidence base | Yes | Train data | No |
| Parallel critics | Yes | N/A | No |
| Web search | Yes (optional) | No | No |
| Open source | Yes | Yes | No |

---

## Cost

**Using the API** (Claude Sonnet): ~$1.50-3.00 for 10 iterations with 4 critics.

**Using Claude CLI** (`--cli` flag, requires Max plan): Free for Claude calls. ~$0.30 for Perplexity web search.

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
  research_notes.md    # Accumulated findings from web searches
```

---

## License

MIT
