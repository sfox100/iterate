# How to Evaluate AI in Production - Iteration Program

## What You Are Producing

A blog post (1500-2500 words) arguing that most teams evaluate AI wrong in production,
and proposing a practical alternative. The target audience is engineering leaders and
AI/ML team leads at companies that have deployed AI systems and are struggling with
quality assurance.

The core argument: the standard approach (build eval sets, run them in CI/CD, check
pass rates) misses the failures that matter most - the ones you didn't anticipate when
you built the eval set. Production AI quality requires monitoring for failure patterns
you haven't seen yet, not just testing for ones you have.

This should be opinionated and specific. Use real examples (anonymised or public).
The reader should walk away with a concrete framework they can apply this week.

## Critics

### practitioner: Senior ML Engineer (3 years in production)

You've deployed 4 AI systems to production. Two are working well, two are causing
constant firefighting. You've built eval sets, you run them nightly, and your pass
rates look great. But users still complain. You're exhausted and skeptical of anyone
who claims to have a better approach.

Answer: Does this match your experience? Where is the gap between what the post
describes and what actually happens in your team? What advice would actually help you
vs what sounds good in theory? Would you share this with your team? Keep feedback to
4-6 sentences.

### editor: Tech Blog Editor (Hacker News regular)

You edit a technical blog. You've rejected 90% of submissions because they say things
everyone already knows in slightly different words. You care about: is there a genuinely
new insight here? Is the writing tight? Would this survive the HN comments section?

Answer: What's the one new idea here that hasn't been said before? Where does this
sound like every other "AI quality" post? What should be cut? What would make you
publish this vs reject it? Keep feedback to 4-6 sentences.

### skeptic: VP of Engineering (pragmatist)

You manage 50 engineers. You've heard every pitch about AI quality tooling. You're
deeply skeptical of frameworks that require major process changes because you know
your team won't adopt them. You need something that fits into existing workflows, not
something that replaces them.

Answer: Is this practical for a real engineering team? What would the adoption barrier
be? Where does this underestimate the messiness of real organizations? What's the
simplest version of this advice that would actually work? Keep feedback to 4-6 sentences.

## Settings

- min_words: 1500
- max_words: 2500
- iterations: 10

## Writer Instructions

When improving the post:
- Lead with a specific, concrete example of AI failing in production. Not abstract.
- The framework should fit on one page. If it needs a diagram, it's too complex.
- Include "what to do Monday morning" - specific first steps, not just principles.
- Acknowledge trade-offs honestly. Every approach has costs.
- Use specific numbers where possible (anonymised is fine).
- Write for someone who has shipped AI, not someone learning about it.

## What NOT to Do

- Don't start with "AI is transforming..." or any throat-clearing
- Don't use "landscape", "paradigm", "ecosystem", "holistic"
- Don't propose a framework with more than 4 steps
- Don't assume the reader has unlimited engineering time
- Don't pitch a product or tool (this is about the approach, not tooling)
- Don't summarise the post at the end

## Web Searches

- AI production monitoring evaluation failures 2025 2026
- LLM evaluation production challenges real-world examples
- AI quality assurance beyond eval sets production monitoring
- machine learning production failures case studies
