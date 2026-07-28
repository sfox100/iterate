# Your eval set is a changelog, not a map

A health system I worked with ran an ambient scribe across roughly 340,000 clinical notes in four months. They were disciplined about quality. A 1,200-case eval set, clinician-labelled, run on every model update and every prompt change for fourteen months. Pass rate sat at 96.3%.

Then a physician flagged a note. The transcript said: *"So we talked through the option of a total knee replacement, and I want you to think about it and come back to me."* The note said: *"Patient elected to proceed with total knee replacement."*

Look at what that output does right. Correct section of the note. Correct procedure. Correct laterality. Grammatical, clinically fluent, consistent with the topic of the encounter. It would pass a factuality check keyed to entities, because every entity is real and present in the transcript. It passes a structure check, a formatting check, a hallucination check that looks for invented medications. It fails on one word, and the word carries the entire clinical and medicolegal meaning.

When they went looking, the pattern showed up in about 0.4% of notes containing decision-adjacent language. Call it 1,400 notes over four months, sitting in charts, some already actioned.

The eval set had zero cases testing whether the model preserves modality - the difference between considering, recommending, and deciding. Not because the team was careless. Because until a physician read that note, nobody on the team had ever thought of it. You cannot write a test case for a failure mode that has not yet occurred to you.

The pass rate was 96.3% throughout. It was measuring the wrong thing, with excellent precision.

## The structural problem, not the execution problem

Every team that hits this reaches for the same fix: more eval cases. It doesn't work, and it doesn't work for reasons that are architectural rather than effortful.

**Eval sets are retrospective by construction.** An eval case is a record of a failure you already survived or already anticipated. Which means the set is at maximum usefulness *after* an incident and near-zero usefulness *before* one. Your eval suite is a changelog of things that went wrong. Changelogs are useful. They are not maps of where you are going.

**The arithmetic is brutal for rare failures.** Take a failure mode that fires at 1 in 2,000. At 100,000 requests a day, that's 50 a day, over 18,000 a year, and every one is a real user getting a bad answer. Now sample 1,200 cases randomly from production for your eval set. Expected count of that failure in your set: 0.6. More than half the time, your set contains zero examples. And your set isn't randomly sampled anyway - it's curated toward cases you thought of, which biases it further away from the ones you didn't.

**The gate framing imports an assumption that doesn't hold.** Unit tests work as binary gates because the specification is written down and complete. For AI systems the specification is implicit, contextual, and continuous. An output can be right for one user and wrong for another. There is no threshold that cleanly separates "ship" from "don't ship," so teams pick one, and then the number the gate produces becomes the thing the team manages.

You can tell you're in this trap by a specific signature: **pass rates are high and user complaints are also high.** That combination is not noise. It's a measurement failure telling you exactly what it is.

## The four classes of failure evals systematically miss

Worth naming them, because they behave differently and need different detection.

**Quietly wrong.** Well-formed outputs that are factually or semantically off in ways requiring domain expertise to see. The scribe case. Also: a legal summariser that gets a clause direction backwards, a financial extractor that reads a credit as a debit. These pass every syntactic check because they are syntactically perfect.

**Boundary violations.** The output is accurate but the system shouldn't have said it. Support agents offering refunds they can't authorise, committing to feature timelines, escalating in ways that create liability. Evals test tone and accuracy; almost nobody writes an eval case for "did the model exceed its authority."

**Aggregate-rare.** Handwritten annotations on invoices. Multi-currency transactions. Documents with internally conflicting values. Each is 0.02% of volume and individually not worth a test case. Together they're 7% of your traffic and the source of most of your escalations.

**Slow drift.** Nothing trips any single threshold. Quality degrades two points a month as user behaviour shifts, upstream retrieval indexes stale, or a model version changes underneath you. Gates fire on deltas from a fixed baseline. Drift is designed to be invisible to them.

## The alternative: a discovery loop that runs on production traffic

This fits on one page because it's four moves. If you need a diagram, someone has over-engineered it.

**1. Judge properties, not answers.** An eval case says: for input X, expect output Y. A property judge says: does this output ever assert a decision the source doesn't support? Does it commit to a timeline? Does it drop a stated negative? Properties generalise to inputs you have never seen. Expected-output pairs do not. This is the single change that does the most work, and it's the one most teams skip.

**2. Score production traffic, not the eval set.** Run those judges over a rolling sample of real outputs, continuously, shadowed so nothing blocks. You don't need every request. You need enough per period to detect a rate change, which is a much smaller number than people assume.

**3. Cluster the bottom, don't count it.** The failure *rate* is a vanity metric - it goes up and down and tells you nothing actionable. The *cluster* is the finding. Every week, pull the lowest-scoring 200 outputs, group them by what actually went wrong, and name the groups. A new named cluster is a new failure mode, discovered before a user escalated it. This is the whole engine. Everything else is plumbing around it.

**4. Promote confirmed clusters into the eval set, and only then.** Now the eval set does the job it's genuinely good at: stopping known failures from returning. A regression suite is *supposed* to contain only bugs you've already seen. That's not a limitation, it's the definition. The mistake was ever asking it to do discovery.

Monitoring finds what's new. The eval set prevents what's old from coming back. Two jobs, two systems, and most teams are running one system and expecting both.

## What to do Monday morning

**Monday.** Pull 500 random production outputs from last week. Random, not filtered - not the flagged ones, not the thumbs-down ones, not the ones support escalated. Those are the failures you already know about. Then read 50 of them yourself. You, the person reading this, not an intern and not a model. Ninety minutes. You cannot write a good property judge for a failure mode you have never seen with your own eyes, and this is the only step that gives you that. Write down every output that made you hesitate, even slightly. Don't classify yet.

**Tuesday.** Group the hesitations. You will get three to six clusters; teams reliably do. Name each one in the language of the property violated, not the symptom. "Asserts unstated decisions" beats "knee surgery thing." The property name is what you're about to turn into a judge, so the naming is the work.

**Wednesday.** Write one judge per cluster. Binary, or 1-5 if the failure is genuinely graded. Run each over 2,000 production outputs. You now have a measured rate for every failure mode you found, which is more than you had on Friday.

**Thursday.** Hand-label 50 outputs per judge and check agreement. Use Cohen's kappa or agreement on the positive class specifically, not raw agreement - on a 1% base rate a judge that answers "fine" every single time scores 99% and is worthless. If kappa is below about 0.6, the criterion is ambiguous, not the judge. Rewrite the criterion. This is the step teams skip and then wonder why their numbers are meaningless.

**Friday.** Take the highest-rate cluster and put one number on a dashboard, tracked daily. One. Resist the suite. A single trusted number that moves beats twelve nobody looks at.

That's a week, and it ends with a rate you didn't have, on a failure mode you didn't know about.

## What this costs, honestly

**Judging isn't free, but it's cheaper than you think.** To detect a shift from 1% to 2% at conventional confidence and power, you need roughly 2,300 judged outputs per period. At 100,000 requests a day that's a 2.3% sample. On a small model with a tight judge prompt, that's single-digit dollars a day. The cost that actually bites is engineering time, not inference.

**Your judges will be wrong.** LLM judges have their own error rate, and an uncalibrated judge's absolute numbers are fiction. But a judge that is *consistently* wrong still produces readable deltas, and deltas are what you're monitoring. Report movements, not levels, until you've calibrated. Never put an uncalibrated absolute rate in front of a regulator or a board.

**Human review does not scale, and shouldn't.** It is your calibration layer, not your coverage layer. Budget a fixed few hours a week from someone with real domain expertise, permanently, and don't let it grow to fill the space.

**Shadow evaluation detects, it does not prevent.** By the time your judge scores the output, the user has it. That's a genuine limitation. Prevention comes second, after you know what you're preventing - and you can only build the guardrail once you can name the failure.

**Goodhart comes for judges too.** The moment a judge score becomes an OKR, someone will optimise for the judge. Rotate criteria. Retire judges once their cluster is fixed and covered by regression tests. A judge suite that never changes has stopped measuring and started performing.

**You will find things you cannot fix.** This is the real cost, and it's cultural rather than technical. Knowing your scribe misrepresents modality in 0.4% of notes with no immediate fix is worse for team morale than not knowing. It is considerably better for patients.

## The question you can't currently answer

Most teams can tell you, to two decimal places, what fraction of their anticipated failures they still catch. Almost none have any process at all for the second question: what is happening in production right now that we have not yet named?

The failure that takes you down is, by definition, not in your eval set. Build the loop that finds it.