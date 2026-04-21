# iterate - autoresearch for text

Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) runs 100 ML experiments overnight by iterating on `train.py` against a single metric: validation loss. When the loss drops, keep the change. When it doesn't, revert.

This is the same idea, but for non-code documents - strategy memos, proposals, essays, blog posts. The things you're working on at midnight and wish you had three smart, opinionated people arguing about in the next room.

The problem: prose doesn't have val_bpb. There's no numeric score that tells you a strategy document improved. The substitute is **named critic personas with conflicting agendas** who each try to find the fatal flaw from their perspective.

---

## The pattern

```
                    ┌─────────────────────────────────────┐
                    │  WRITER (Claude, tools disabled)     │
                    │  Reads: document + critic feedback   │
                    │  + evidence base + web research      │
                    │  Picks 2-3 strongest objections      │
                    │  Makes surgical improvements         │
                    │  Outputs: complete improved document  │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  2-5 CRITICS (parallel, independent) │
                    │  Each has a specific persona + agenda │
                    │  Each gets: evidence + web research   │
                    │  Each outputs: 4-6 sentences feedback │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                         Length gate only
                    (reject if document collapsed)
                         Feedback feeds forward
                                   │
                                   ▼
                              Next iteration
```

Five inputs:
1. **program.md** - what you're optimising for (the brief, the audience, the critic personas)
2. **evidence/** - curated context files (research, transcripts, data, reference material)
3. **document.md** - the thing being improved
4. **Critic feedback** - from the previous round
5. **Web search results** - fresh context from the internet (optional)

One output: an improved document, every version saved.

---

## The seven design decisions

These emerged from running 50+ critic personas across 30+ iteration rounds on different types of content (strategy documents, sales proposals, blog posts, outbound messages, product specs). Each one represents a wrong approach we tried first.

### 1. No quality scoring gate

**What didn't work:** Scoring each iteration on a 0-1 scale and rejecting anything that dropped below the previous best. This created a plateau - 7 consecutive rejections at score 0.78, because the scores measured text properties (coherence, evidence engagement) not actual document quality.

**What works:** Feedback-only. Critics give prose feedback, never scores. The writer addresses it. Always accept the new version unless the document literally collapsed (fell below a minimum word count). The length gate catches catastrophic failure; everything else is handled by the feedback loop itself.

**Why:** Quality scores for prose are noisy and measure the wrong thing. A critic asking "would I actually invest in this?" is testing strategic quality. A scoring rubric checking "does it engage with contradicting evidence?" is testing text properties. The critic is closer to what matters.

### 2. Surgical improvements, not full rewrites

**What didn't work:** Telling the writer "you may restructure any section." This produced complete rewrites each iteration, regressing dimensions that were already strong. A section that was working well would get rewritten to address one critic's feedback and lose what made it good.

**What works:** "Copy sections that are already strong verbatim. Only modify the parts that need improvement." The writer picks 2-3 of the strongest critiques and addresses them surgically. Everything else stays unchanged.

**Why:** Good writing is a high-dimensional object. Rewriting from scratch re-rolls all dimensions. Surgical edits improve the targeted dimensions while preserving what's working.

### 3. Writer picks which critics to address

**What didn't work:** Addressing all critic feedback in every iteration. With 4-5 critics, this overwhelmed the writer and produced shallow responses to all feedback rather than deep responses to the most important points.

**What works:** The writer reads all feedback, then picks the 2-3 strongest objections to address in this round. The others get addressed in subsequent rounds. This creates natural prioritisation - structural problems get fixed first, then gaps, then nuance.

**Why:** Addressing five critics at once is like trying to satisfy five stakeholders in a single meeting. You end up with a compromise that pleases nobody. Sequential prioritisation produces deeper improvements.

### 4. Curated evidence, not raw dumps

**What didn't work:** Feeding the writer 500KB+ of raw transcripts and notes. The model produced thin, generic outputs because it couldn't synthesise across that volume effectively.

**What works:** Condensed summaries. A 685KB transcript archive becomes a 13KB summary of key insights. The total evidence base should be roughly 100-300KB of curated, structured material. If it doesn't fit comfortably in context, it's too much.

**Why:** The model's attention is finite. If you give it 50 pages of notes, it will latch onto whatever is most salient rather than what's most relevant. Curating the evidence is an act of editorial judgment that dramatically improves output quality.

### 5. Named personas, not generic roles

**What didn't work:** "A venture capital investor evaluates the strategy." Generic roles produce generic feedback.

**What works:** "You are a Series A investor at a top-tier fund. You've seen 200+ startups this year. You care about: market size, defensibility, team-market fit, and speed to revenue. Would you fund this?" Named experts with specific opinions, track records, and agendas produce feedback that creates genuine tension.

**Why:** A named persona with a backstory and specific concerns generates structurally different critiques than a role description. The investor who has "seen 200+ startups this year" will flag pattern-matching problems. The CTO who has "to build whatever this says" will flag feasibility problems. These are different failure modes, not just different labels.

### 6. Critics must have conflicting agendas

**What didn't work:** Four critics who all want the same thing (a better strategy document). They converge on the same feedback and the loop stagnates.

**What works:** Critics with structurally different agendas that create genuine tension:
- The **investor** wants scale and speed - "is this a \$100M outcome?"
- The **customer** wants proof and specificity - "what sounds like every other vendor pitch?"
- The **CTO** wants realism - "can we actually build this with our team?"
- The **sales advisor** wants urgency - "who has a burning project THIS QUARTER?"

The investor pushes for ambition; the CTO pushes for realism. The customer pushes for proof; the sales advisor pushes for urgency. These tensions can't be resolved by tweaking one section. They force the writer to make real strategic choices.

**Why:** The value of multiple critics isn't redundancy - it's productive disagreement. If your critics agree, you effectively have one critic.

### 7. Pre-executed searches beat model tool-use

**What didn't work:** Giving the model access to evidence_search and web_search tools within a single stateless API call. Multi-turn tool use in a stateless CLI invocation (`claude -p`) is unreliable.

**What works:** Run the searches in Python before the API call and inject the results directly into the prompt. The model gets "here's what I found when I searched for X" rather than needing to call a tool mid-response.

**Why:** This is a pragmatic engineering choice, not a fundamental limitation. Pre-executed searches are deterministic, debuggable, and don't depend on the model correctly using tools in a stateless context. They also let you parallelise the search work.

---

## The iteration curve

Across different types of content, a consistent pattern emerged:

**Phase 1 (iterations 1-2): Fix what's WRONG**
The first round catches structural problems, misaligned framing, jargon, voice violations. What any competent editor would catch on a first read. This is the biggest single improvement.

**Phase 2 (iterations 3-5): Find what's MISSING**
The second phase identifies gaps - missing scenarios, absent trust signals, missing edge cases, areas that need evidence rather than assertion. This requires deeper interrogation from the critics.

**Phase 3 (iterations 6-8): Handle the SKEPTIC**
The third phase adds intellectual honesty - acknowledging what competitors do well, addressing edge cases, engaging with the strongest counterarguments. Invisible to friendly readers, essential for hostile ones.

**Phase 4+ (iterations 8+): Diminishing returns**
After 8-10 iterations, improvements become marginal. The ceiling is real-world data. A strategy document can only get so good without actual customer feedback, reply rates, or deployment results. This is the signal to stop iterating and start testing in the real world.

**Implication:** 8-10 iterations is the sweet spot for most documents. Going to 20 is fine if you're running it overnight, but don't expect phase 3+ gains to match phases 1-2.

---

## Other things we learned

**Cutting beats adding.** The biggest improvements often came from removing sections, not adding them. Cutting a pitch-y ending, removing a jargon-heavy table, deleting a section that restated something already said. If a critic says "this feels like padding," the answer is usually to cut, not to rewrite.

**Batch problems are invisible at individual level.** When iterating on a set of outbound messages (13 at once), each message individually looked fine. But a critic who read all 13 together flagged template sameness that was invisible at the individual level. If you're iterating on a batch, have at least one critic read the entire batch.

**Voice consistency is the hardest thing to maintain.** AI-written prose drifts toward polished corporate language with every iteration. The voice gets smoother, more generic, more "professional." If you have a specific voice you want to maintain, include voice instructions and have one critic specifically watching for drift.

**The ceiling is real-world data.** Every type of content hit a quality ceiling around the same point - the writing couldn't improve further without named customers, reply rates, engagement data, or deployment results. The iteration loop is pre-launch refinement. Post-launch, iterate with real data.

**High-quality starting documents have low iteration ceilings.** A document that's already good (started at quality ~4.7/5) gained only 0.15 over 4 rounds. A rough first draft (started at ~3.5/5) gained 1.0+ over the same rounds. This tool is most valuable when starting from a rough draft, not polishing a near-final version.

---

## How to write good critic personas

The critics are the engine. Bad critics produce generic feedback that doesn't improve the document. Good critics produce specific, actionable tension that forces real decisions.

**Rules of thumb:**
- Each critic should have a **structurally different agenda** from every other critic. If two critics want the same thing, merge them.
- Give critics a **backstory that creates specific opinions.** "An investor" is generic. "An investor who has seen 200+ AI startups this year and passes on 95% of them" has opinions.
- Tell critics to **keep feedback to 4-6 sentences.** Longer feedback gets generic. Short feedback stays sharp.
- The best critic is one who **disagrees with the premise**, not just the execution. "Could you build this yourself in 3 months?" forces a fundamentally different response than "is this well-written?"
- Include one **internal voice** (someone who has to build/deliver what the document proposes). This prevents the document from promising things that can't be delivered.

---

## Cost and runtime

Using the Anthropic API with Claude Sonnet:
- ~\$0.02-0.05 per critic call (depending on evidence size)
- ~\$0.05-0.10 per writer call
- ~\$0.01 per Perplexity web search (optional)
- **Total per iteration:** ~\$0.15-0.30 with 4 critics
- **10 iterations:** ~\$1.50-3.00
- **Runtime:** ~3-5 minutes per iteration (critics run in parallel), so 10 iterations = 30-50 minutes

Using `claude -p` with a Claude Max subscription:
- All Claude calls are free (included in the subscription)
- Only cost is Perplexity web search (~\$0.03/iteration)
- **10 iterations:** ~\$0.30 (Perplexity only)
- **Runtime:** ~5-10 minutes per iteration (CLI has more overhead), so 10 iterations = 50-100 minutes

---

## When NOT to use this

- **Urgent one-shot tasks.** If you need something in the next hour, use Claude directly with good prompts. The loop is for overnight refinement, not real-time work.
- **Fully autonomous high-stakes content.** Someone should review the output before it goes to a client or gets published. The loop improves quality but doesn't guarantee correctness.
- **Tasks with numeric metrics.** If you can actually measure quality (A/B test results, accuracy scores, conversion rates), use those metrics directly. The critic loop is for when you can't measure quality objectively.
- **Near-final polishing.** If the document is already 90% there, you'll get marginal returns. The biggest gains come from rough drafts.

---

## How this differs from other approaches

| | iterate | Karpathy's autoresearch | Adversary Loops | Standard prompting |
|---|---|---|---|---|
| **Domain** | Prose/strategy | ML code | Prose (single critic) | Anything |
| **Metric** | Named critic feedback | val_bpb (numeric) | Anonymous critique | Human judgment |
| **Critics** | 2-5 named personas | N/A (metric only) | 1 anonymous | N/A |
| **Evidence base** | Yes (curated files) | Train data | No | Conversation context |
| **Parallel critics** | Yes | N/A | No | N/A |
| **Version tracking** | Yes (all versions saved) | Yes (git) | No | No |
| **Web search** | Yes (optional) | No | No | No |
| **Cost (10 iterations)** | \$1.50-3.00 or free (Max) | Free (local GPU) | \$15/mo subscription | Free |
| **Open source** | Yes | Yes | No | N/A |
