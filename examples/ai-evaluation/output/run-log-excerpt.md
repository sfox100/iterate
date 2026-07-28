# Run log excerpt - critic feedback evolving

These are the writer's own change summaries and the **editor** critic's "one new
idea" verdict, round by round, taken verbatim from the run (`run_log.md` and
`experiments.jsonl`). The editor was the sharpest critic here, so tracking one
line across the run shows the loop working: a buried claim in the seed gets
promoted, sharpened, and finally becomes the title.

Full critic output for every round is longer than what's quoted here; these are
the load-bearing snippets.

---

## Seed (v000) - 1,767 words

> **editor:** The one new idea is "judge properties, not answers" - specifically
> the claim that a property generalises to inputs you've never seen while an
> expert-labelled case does not. [...]

The insight is present, but buried in the middle of the post.

## Iteration 1 -> 2,271 words

> **writer:** I addressed the editor's sharpest structural objection - that
> clustering judge-scored outputs can't surface unknown unknowns and contradicts
> the random-sampling step - by making the human read of unfiltered outputs the
> spine of the method.

> **editor:** The one genuinely new idea: judges never discover, they only scale.
> The closed-loop argument in step 1 - a judge-ranked list is by construction
> sorted by properties you've already named, so the bottom of it is a list of
> failures you already know about - is the load-bearing claim, and it's sharper now.

## Iteration 2 -> 2,428 words

> **writer:** Addressed the editor's structural cut (sections 1-2 compressed from
> ~820 words to ~560, Goodhart and shadow-eval bullets dropped, the "stable broken
> judge" line pulled up to 45% depth).

> **editor:** The one new idea: the negative claim buried in the middle - judges
> scale a finding, they never make one, so a property judge generalises across
> inputs you've never seen but never across failure modes you've never named.

## Iteration 3 -> 2,633 words (final)

> **writer:** I cut the first two sections by ~60% (the editor's core objection:
> 700 words of received wisdom restated four ways) and promoted the negative claim
> to the front.

> **editor:** The new idea: judges generalise across inputs you've never seen but
> never across failure modes you've never named, and the instance-vs-rule framing
> that follows it ("an eval case tests an instance; a judge tests a rule") is the
> one thing here I haven't read elsewhere.

---

**The arc:** the seed's strongest idea was a claim sitting in the middle of the
post. Three rounds of critic pressure cut ~700 words of generic setup, promoted
that claim to the lead, and forged the framing that became the final title -
*"Your judge will never find the failure you haven't named."* No numeric score
gate; the length gate never fired (every version was kept). Pure feedback.
