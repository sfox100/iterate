# Common Pitfalls in AI Evaluation

## Pitfall 1: Eval sets test what you already know

The fundamental problem with curated eval sets: they can only test for failure modes
you've already identified. They are retrospective by nature. Production failures are
prospective - they're the things you haven't seen yet.

This creates a paradox: the eval set is most useful after the failure has already
happened (you add a test case for it), and least useful before it happens (it's not
in the set).

## Pitfall 2: High pass rates create false confidence

A 95% pass rate on an eval set means the model handles 95% of your ANTICIPATED
scenarios. It says nothing about scenarios you didn't anticipate. Teams often
conflate "passes our evals" with "works well in production."

The dangerous state is: pass rates are high AND user complaints are also high.
This means the eval set is measuring the wrong thing.

## Pitfall 3: Eval set maintenance becomes the product

As teams add more eval cases to cover observed failures, the eval set grows. At some
point, maintaining the eval set (writing cases, reviewing results, updating thresholds)
consumes more engineering time than building the product.

Signs you're in this trap:
- More than 50% of "AI quality" time goes to eval maintenance
- Adding eval cases doesn't reduce production incidents
- Nobody can explain what the eval set actually covers vs doesn't cover

## Pitfall 4: Treating evaluation as a gate vs a signal

The CI/CD model treats evaluation as a binary gate: pass or fail. This works for
unit tests because the specification is known. It doesn't work for AI because:
- Quality is continuous, not binary
- Context matters (an output can be good for one user and bad for another)
- The specification is often implicit (no one wrote down exactly what "good" means)

Treating evaluation as a signal (monitoring trends, flagging anomalies, sampling for
review) is often more useful than treating it as a gate.

## Pitfall 5: Ignoring the "quietly wrong" failures

The most dangerous AI failures are not errors or crashes. They're outputs that look
correct but aren't - hallucinated facts, subtly wrong recommendations, plausible but
inaccurate summaries. These pass automated checks because they're well-formed. They
fail users because they're wrong in ways that require domain expertise to detect.

Standard evaluation approaches are weakest at exactly this type of failure.

## Pitfall 6: Optimising for the metric instead of the outcome

When eval metrics become the target, teams optimise for the metric rather than the
outcome. A model that scores well on your eval benchmark may have learned to produce
outputs that satisfy the evaluation criteria without actually being useful to users.

This is Goodhart's Law applied to AI evaluation: when a measure becomes a target,
it ceases to be a good measure.
