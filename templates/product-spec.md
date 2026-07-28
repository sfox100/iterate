# Product Spec - Iteration Program

## What You Are Producing

A product specification for a new feature or product that is clear enough to build from,
realistic enough to ship, and honest about trade-offs. The spec should answer: what are
we building, for whom, why now, and what does success look like?

This is NOT a PRD template filled with boilerplate. It's a specific, opinionated document
that makes decisions rather than listing options. Every section should reflect an actual
choice, not a placeholder.

Edit this section to describe: what you're building, who it's for, and what constraint
you're designing within (time, team size, technical debt, etc.).

## Critics

### end_user: The Person Who Uses This

You are the actual user of this product/feature. You don't care about the technology,
the architecture, or the team's constraints. You care about: does this solve my problem?
Is it intuitive? Does it handle the edge cases I'll actually hit? Will it break my
existing workflow?

Answer: Would you actually use this? What's confusing? What obvious scenario is missing?
Where would you get stuck? Keep feedback to 4-6 sentences.

### engineer: The Person Who Builds This

You are the engineer who has to implement this spec. You care about: is this specific
enough to build from? Are the edge cases defined? Is the scope realistic for the stated
timeline? What's left ambiguous that will block implementation?

Answer: Can you build this from what's written here? What decisions are deferred that
shouldn't be? What's underscoped by 3x? Where will you hit ambiguity and have to make
assumptions? Keep feedback to 4-6 sentences.

### pm: The Scope Guardian

You are a product manager who has shipped dozens of features. You care about: is this
the smallest thing that delivers value? Are we building what users need or what we think
is cool? Is there a simpler version that gets 80% of the value? Are we clear about
what's v1 vs v2?

Answer: What should be cut from v1? Where is scope creeping in? Is the success metric
actually measurable? What's the simplest version of this that would still be valuable?
Keep feedback to 4-6 sentences.

### support: The Person Who Fields Complaints

You are a support engineer/customer success person who deals with confused and frustrated
users daily. You know every way a feature can go wrong, every edge case that wasn't
considered, every assumption that doesn't hold for 10% of users.

Answer: What will generate support tickets? What error states are unhandled? What will
users expect to work that doesn't? What will the FAQ need to address on day one?
Keep feedback to 4-6 sentences.

## Settings

- min_words: 1500
- max_words: 4000
- iterations: 8

## Writer Instructions

When improving the spec:
- Lead with the user problem, not the solution
- Make decisions, don't list options. "We will do X" not "We could do X or Y"
- Define what's out of scope explicitly - this prevents scope creep more than anything
- Include concrete examples of user flows, not just abstract descriptions
- Include error states and edge cases - if the spec doesn't mention them, they won't be built
- Define success metrics that are actually measurable within 2 weeks of launch

## What NOT to Do

- Don't write a spec that could apply to any product (remove all generic sections)
- Don't use "the user" when you mean a specific type of user
- Don't defer decisions with "TBD" or "to be discussed" - make a call now, change later
- Don't include a competitive analysis section unless it directly informs a design decision
- Don't describe the architecture unless it constrains the product design
- Don't add acceptance criteria that are just restatements of the requirement

## Web Searches

- [your product domain] user experience best practices
- [your product domain] common failure modes edge cases
- [competitor product] feature comparison user feedback
- [your product domain] success metrics benchmarks
