# Example output: a real run

This directory is the unedited output of running `iterate` on the example in the
parent directory - the [`program.md`](../program.md) brief (a blog post arguing
that most teams evaluate AI wrong in production) with the two files in
[`evidence/`](../evidence/) as context.

```bash
cd examples/ai-evaluation
python ../../iterate.py --cli --max-iterations 3
```

Run on 2026-07-28 via `--cli` (Claude Max plan, no API spend), 3 critics
(practitioner, editor, skeptic), 3 iterations. Nothing here is hand-edited.

## What to look at

| File | What it is |
|------|-----------|
| [`v000-seed.md`](v000-seed.md) | The **seed** - first draft, generated cold from the brief + evidence (1,767 words) |
| [`final.md`](final.md) | The **final** document after 3 iterations (2,633 words) |
| [`run-log-excerpt.md`](run-log-excerpt.md) | The critic feedback evolving round by round |

## The before/after in one line

The seed was already a solid draft - same knee-replacement opening as the final.
What changed is where the argument lives. The seed's title was a general metaphor
and its load-bearing claim sat in the middle of the post. Three rounds of critic
pressure cut ~700 words of setup ("received wisdom restated four ways", per the
writer), promoted that claim to the lead, and sharpened it into a title the editor
critic called "the one thing here I haven't read elsewhere":

- **Seed title:** *Your eval set is a changelog, not a map*
- **Final title:** *Your judge will never find the failure you haven't named*

The document did not simply get longer. Sections 1-2 were compressed by ~60% while
the core argument was surfaced and sharpened - exactly the "surgical edits, not
rewrites" behaviour the technique is built around. No numeric scoring was involved;
the length gate (the only automatic reject) never fired.

> Full transparency: 3 iterations is a short run chosen to keep the example cheap
> and readable. The [README](../../README.md) suggests 8-10 for real work. Diminishing
> returns start around iteration 6-8 - see [TECHNIQUE.md](../../TECHNIQUE.md).
