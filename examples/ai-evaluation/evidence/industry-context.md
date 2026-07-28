# AI Evaluation in Production - Industry Context

## The standard approach and its limits

Most teams building AI products follow a standard evaluation workflow:
1. Build a curated eval set (golden examples with expected outputs)
2. Run evals in CI/CD before deployment
3. Check pass rates against thresholds
4. Deploy if pass rates meet the bar

This works for catching regressions in known failure modes. It doesn't work for:
- Failures you didn't anticipate when building the eval set
- Distribution shift (production inputs differ from eval inputs)
- Edge cases that are rare individually but common in aggregate
- Gradual quality degradation that doesn't trigger any single threshold

## Public examples of production AI failures

### Customer support AI
Multiple reports of customer support AI systems making unauthorised commitments -
offering refunds, making promises about product features, escalating in ways that
created liability. Eval sets tested for tone and accuracy but not for boundary
violations around authority and commitments.

### Medical AI scribes
AI medical scribes that pass clinical accuracy benchmarks but introduce subtle errors
in production: documenting discussions as decisions ("discussed surgery" becomes
"decided on surgery"), omitting relevant negatives, generating plausible-sounding
medications that weren't mentioned. These pass standard NLP evaluations because the
text is grammatically correct and contextually plausible.

### Code generation
Code generation tools that produce syntactically correct code that passes unit tests
but introduces subtle security vulnerabilities, uses deprecated APIs, or creates
maintainability issues. Standard evals check for correctness; production failures are
about everything else.

### Financial services
AI systems processing financial documents that work well on standard document formats
but fail on edge cases: handwritten annotations, multi-currency transactions, documents
with conflicting information. Eval sets tested the common cases; production exposed
the long tail.

## What practitioners say

Recurring themes from engineering teams in production:
- "Our eval pass rate is 94% and users still complain weekly"
- "We added 200 more eval cases and it didn't reduce production incidents"
- "The failures that matter are always the ones we didn't think to test for"
- "We spend more time maintaining eval sets than building features"
- "We know something is wrong but we can't measure it"

## The monitoring gap

Most AI observability tools focus on infrastructure metrics (latency, throughput,
error rates) or model metrics (accuracy, F1, BLEU). Few address the gap between
"the model produced output" and "the output was actually good for the user's purpose."

This gap is where most production AI quality problems live. The model is working
correctly by its own metrics. It's just not doing what the user needed.

## Emerging approaches

Several patterns are emerging for addressing production AI quality:
- **Human-in-the-loop sampling**: Review a random sample of production outputs
- **LLM-as-judge**: Use a second model to evaluate production outputs
- **User feedback signals**: Track downstream user actions as quality proxies
- **Failure taxonomy development**: Categorise observed failures to build targeted eval sets
- **Shadow evaluation**: Run evaluation in production without blocking the user

Each has trade-offs around cost, coverage, latency, and accuracy of the quality signal.
