# Your judge will never find the failure you haven't named

A health system I worked with ran an ambient scribe across roughly 340,000 clinical notes in four months. They were disciplined about quality: a 1,200-case eval set, clinician-labelled, run on every model update and every prompt change for fourteen months. Pass rate sat at 96.3%.

Then a physician flagged a note. The transcript said: *"So we talked through the option of a total knee replacement, and I want you to think about it and come back to me."* The note said: *"Patient elected to proceed with total knee replacement."*

Look at what that output does right. Correct section, correct procedure, correct laterality. Grammatical, clinically fluent, consistent with the topic of the encounter. It passes a factuality check keyed to entities, because every entity is real and present in the transcript. It passes structure, formatting, and a hallucination check looking for invented medications. It fails on one word, and the word carries the entire clinical and medicolegal meaning.

When they went looking, the pattern showed up in about 0.4% of notes containing decision-adjacent language. Call it 1,400 notes over four months, sitting in charts, some already actioned. Identifying details are changed and these numbers come from one deployment, so don't take 0.4% as a base rate for yours. The mechanism is the part you check against your own logs, and the arithmetic below holds at whatever rate you plug into it.

The eval set had zero cases testing whether the model preserves modality: the difference between considering, recommending, and deciding. Not because the team was careless. Because until a physician read that note, nobody had thought of it. The pass rate was 96.3% throughout. It was measuring the wrong thing, with excellent precision.

## More eval cases won't fix this

An eval case records a failure you already survived or already anticipated, which makes your suite a changelog. Changelogs are useful. They are not maps.

The arithmetic is worst for exactly the failures you care about. Take a failure mode that fires at 1 in 2,000. At 100,000 requests a day that's 50 a day and over 18,000 a year, every one a real user getting a bad answer. Now sample 1,200 cases from production for your eval set. Expected count of that failure in the set: 0.6. More than half the time it contains zero examples, and your set isn't randomly sampled anyway - it's curated toward cases you thought of, which biases it further from the ones you didn't.

One signature tells you you're here: **pass rates are high and user complaints are also high.** That combination is not noise. It's a measurement failure announcing itself.

## What a judge can and cannot do

Start with the limit, because almost everything written about LLM judges implies the opposite. **A judge generalises across inputs you have never seen. It never generalises across failure modes you have never named.** Judges scale, measure and watch a finding you already made by hand. They do not make it.

Inside that limit they're powerful. An eval case tests an instance; a judge tests a rule. *For input X, expect output Y* can only ever fire on X. *Does this note assert a decision the transcript doesn't support?* is answerable on a note about a knee replacement, a statin, a referral, a phone consult, a specialty nobody enumerated. The instance doesn't transfer. The rule does. Once "asserts unstated decisions" exists as a question, the judge finds it in phrasings nobody thought of, and that is most of the value. It will still never find the thing you haven't named.

Which is why the first judge that team wrote looked so reasonable:

```
Rate the clinical accuracy of this note against the transcript on a
scale of 1-5, where 5 is fully accurate and 1 is seriously misleading.
```

It ran for three weeks and looked healthy. Mean around 4.3, low variance, no alarming trend, a nice flat line on a dashboard. Then two clinicians labelled the same 50 notes and agreed with each other at a kappa just over 0.3 - roughly what you get from two people answering different questions.

They were. "Accuracy" bundles at least five distinct properties: omission, invention, wrong attribution, wrong modality, wrong emphasis. One reviewer was mostly scoring invented content. The other was mostly scoring missing content. Both were right about different things, and the average of their two answers meant nothing at all.

**A broken judge that is stable looks exactly like a healthy one.** Three weeks of a flat line is not evidence of quality. It is evidence that whatever the judge is measuring, it is measuring consistently.

Here is the rewrite, close to verbatim:

```
You will see a transcript excerpt and the generated clinical note.

Question: does the note assert that a decision was made, when the
transcript shows only that an option was discussed, recommended,
or deferred?

Answer YES only if BOTH hold:
 (a) the note uses decision language about a procedure, medication,
     referral or plan - "elected", "will proceed", "agreed to",
     "started on", "declined"; and
 (b) the strongest corresponding language in the transcript is
     deliberative - "discussed", "offered", "we could", "think
     about it" - or the patient defers to a later conversation.

Answer NO if the transcript contains explicit patient assent
("yes, let's do it", "go ahead and book it") or an unambiguous
clinician directive the patient does not contest.

If you cannot tell whether assent occurred, answer UNCLEAR.
Do not guess.
```

Same notes, same two reviewers, kappa just over 0.7. Nothing changed about the model, the data, or the people. The question changed. When agreement is bad, the criterion is ambiguous far more often than the judge is stupid. Rewrite the question before you touch the model.

## The loop, in four moves

**1. Read random production outputs yourself.** Unfiltered. Not the flagged ones, not the thumbs-down, not the support escalations - those are the failures you already know about. You, the person reading this, not an intern and not a model. Fifty outputs, ninety minutes. Write down everything that made you hesitate, even slightly. Don't classify yet.

**2. Name the property that was violated, not the symptom.** You'll get three to six clusters; teams reliably do. "Asserts unstated decisions" beats "knee surgery thing." The name is what becomes the judge, so the naming is the work.

If the system spans three teams - prompt owned by product, model config by platform, review queue by ops - naming is where this dies. You get two competing taxonomies and a fortnight of argument about categories. Don't run it as a consensus exercise. Whoever did the reading names the clusters alone and presents them, and the name only has to be good enough to write one judge against. Take the highest-rate cluster, ship that judge, and let it produce a number. A judge that catches something real ends the taxonomy argument in a way no meeting will.

**3. Write one judge per cluster, and check it before you believe a single number it produces.** Binary where you can. Then take 20 outputs the judge called positive and 20 it called negative, read them yourself, and count how many you disagree with. That's the whole check: forty outputs, forty minutes, no statistics. More than about four disagreements and the criterion is ambiguous - rewrite it and count again. Split the sample deliberately, because at a 1% base rate a judge that answers "fine" every time scores 99% and is worthless; the 20 positives are where it dies. If you have someone who will compute kappa on a properly labelled sample, better. But a crude check that happens beats a rigorous one that gets skipped, and this is the step teams skip. Skipping it doesn't give you a weak number. It gives you a flat line that means nothing, and you will believe it.

**4. Put one number on a dashboard, and promote confirmed failures into the eval set.** One number, tracked daily, from your highest-rate cluster. Resist the suite. Then the eval set does the job it's genuinely good at: stopping known failures from coming back. A regression suite is *supposed* to contain only bugs you've already seen. That's the definition, not a limitation. The mistake was ever asking it to do discovery.

Note what step 1 is not. It is not "review the flagged outputs," and it is not "cluster the lowest-scoring outputs from your judges." Both are tempting and both are closed loops - your judges only score properties you have already named, so the bottom of a judge-ranked list is, by construction, a list of failures you already know about. Scoring is not discovery. Unfiltered traffic plus a human who knows the domain is the only discovery channel you have.

Step 1 is Hamel Husain's error analysis, essentially unmodified, and the calibration failure above is a cousin of what Shreya Shankar's group named criteria drift: you cannot specify good criteria until you have graded outputs, so criteria have to be built by grading rather than written up front. Neither is mine. The negative claim is the part I'd add.

Which means step 1 never stops, and that's exactly where it would be easy to rebuild the treadmill I just spent two sections attacking. A standing weekly "review the bottom 200" is eval maintenance in a new coat: unbounded, growing, owned by nobody.

So don't create a ritual. Bolt the hour onto a meeting that already exists, already has an owner and already has an agenda, as a standing item whose output is one written pattern. If it didn't happen, it's visible in that agenda that week. That's the mechanism - not somebody's vigilance, which is a description of the problem rather than a fix. Monthly that actually happens beats weekly that doesn't. Judges retire: once a failure mode is fixed and covered by a regression case, its judge comes off the dashboard.

And the hour has to come from somewhere. Take it from eval-set maintenance. Stop writing new eval cases for a month - not the ones that encode confirmed incidents, the speculative ones you write to raise coverage. If the arithmetic above is right, those hours were the lowest-yield hours you spend on quality, which makes them the ones to spend here.

## If you have four systems and two are on fire

Run this on one that isn't burning.

That sounds like the cowardly answer and it's the correct one. A system that's on fire has *named* failures. You know what's wrong with it, you have tickets, and the fix budget is already allocated. Discovery buys you nothing there. It pays exactly where the dashboards are green, the complaints are a low background hum, and nobody can tell you why. That's the system with an unnamed 0.4% in it.

The burning systems still get something from this, just not step 1. Take whatever judges or scores you're already trusting on them and run the 40-output check from step 3. Half the time you'll find you've been reading a flat line.

If you can't get raw production outputs onto a screen without a two-week PHI or legal review, file that request today and don't let it block the ninety minutes. Things you can usually read this week: whatever de-identified corpus your annotation vendor already holds, staging traffic driven by real inputs, or the outputs already sitting in support tickets. That last one is biased toward known failures and won't give you discovery, but it will give you a first judge to calibrate, so the calibration work is done when access lands.

And if your total budget is 200 outputs and 40 minutes of a clinician's time: spend zero of the clinician's minutes on discovery reading. An engineer with moderate domain sense can do that. Spend all 40 on labelling for calibration, because that is the only step that genuinely requires expertise you don't have. Accept that 200 outputs cannot measure a 1% failure rate, so don't quote one.

## Getting a 0.4% funded

Two different asks, and conflating them is what sinks this.

The discovery is not a workstream and must never be presented as one. An hour of one engineer's time on an existing agenda needs no budget line, no headcount and no prioritisation decision - and the moment it appears in a prioritisation meeting it loses, because it's competing against fire and it has no ticket, no angry account and no pager. Anything that has to win that meeting to happen will not happen. Don't take it there. Take the artefact there, afterwards.

The fix is a real ask, and by then you have what you need to win it. Convert the rate into a count over elapsed time, because 0.4% sounds like rounding and "1,400 notes, some already actioned" does not. Bring one instance, transcript on the left and note on the right, because the knee-replacement pair does more work in a room than any number will. Name the asymmetry directly: an outage has a bounded blast radius and a known end time, while this has run for fourteen months and has no natural end, because nothing about it triggers an alert.

Then size the ask to slack that actually exists. "Route decision-adjacent notes into the review queue" is an engineering ask only if that queue has capacity; 1,400 items into human review is a headcount conversation wearing an engineering costume. So ask ops what the queue absorbs today, take that number, and route the highest-confidence slice that fits it. If the answer is zero, the ask becomes a flag on the note rather than a review of it. One engineer, two weeks, containment on a known rate.

## What this costs

**Judging isn't free, but it's cheaper than you think.** To detect a shift from 1% to 2% at conventional confidence and power you need roughly 2,300 judged outputs per period. At 100,000 requests a day that's a 2.3% sample - single-digit dollars a day on a small model with a tight prompt. The cost that bites is engineering attention, not inference.

**Writing the number down creates a document.** "0.4% of notes misstate a clinical decision" is discoverable in litigation, and in regulated industries this is what kills the programme - legal, not engineering. It's also the one dependency you can't route around, since counsel doesn't report to you and a privilege review is measured in weeks.

So notice what actually needs the review. Steps 1 to 3 produce reading notes and a judge prompt. Step 4 produces a *rate*, and a rate is the only artefact anyone will ever subpoena. Counsel gates step 4, not the ninety minutes. File the request the same week you do the first read and let the two run in parallel. The framing that usually works is quality improvement under existing privilege, with retention agreed up front: who holds the numbers, for how long, and what happens to the intermediate ones. Get that wrong and you'll be told to stop measuring, which is a worse outcome than any number you'd have found.

**You will find things you cannot fix.** This is the real cost and it's cultural. Knowing your scribe misrepresents modality in 0.4% of notes with no immediate fix is worse for team morale than not knowing. It is considerably better for patients.

## The question you can't currently answer

Most teams can tell you to two decimal places what fraction of their anticipated failures they still catch. Almost none have any process at all for the second question: what is happening in production right now that we have not yet named?

The failure that takes you down is, by definition, not in your eval set. Somebody has to go and read.