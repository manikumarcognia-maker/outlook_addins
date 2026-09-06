# Coding Standards & Protocol for Cursor

Paste this into every new Cursor project as a standing instruction (or save
it as `.cursorrules` in the repo root so it applies automatically). This is
not tied to any specific project — it governs *how* code gets written,
regardless of what's being built.

---

## Core Principle

**Write the simplest code that correctly solves the actual problem in front
of you.** Not the most flexible, not the most "enterprise," not the most
impressive-looking — the simplest one that's correct, readable, and
maintainable. Every rule below is downstream of this one.

If you (Cursor) ever find yourself adding a layer of abstraction, a config
option, or a design pattern that the current task doesn't actually need,
stop and remove it. Anticipating future requirements that haven't been
asked for is not thoroughness — it's guessing, and guesses add complexity
that has to be maintained whether or not the guess was right.

---

## 1. No Redundant Code

- **Before writing a new function, search the codebase for one that already
  does this or something close to it.** If it exists, use or extend it —
  don't write a parallel version.
- **Never duplicate logic across files "to be safe" or "to avoid touching
  shared code."** Shared logic goes in one place; every caller uses that
  one place. If two pieces of logic look 90% similar, that's a signal to
  extract a shared function, not a reason to write both out separately.
- **Don't regenerate a whole file to make a small change.** If you're
  editing a function, edit that function. Rewriting a full file when three
  lines needed to change makes diffs unreadable and increases the chance of
  silently reverting unrelated work.
- **Delete dead code you find, don't comment it out.** Commented-out blocks
  accumulate and nobody remembers if they're safe to remove. If it's not
  used, remove it (version control already has the history).
- **One source of truth per piece of state or config.** Never let the same
  fact (a URL, a limit, a schema) live in two places that both need to be
  updated in sync — that's how they drift apart.

---

## 2. No Unnecessary Complexity

- **Do not introduce a design pattern, abstraction layer, or framework
  feature unless the current requirement actually needs it.** A factory,
  a plugin system, a generic base class — these are justified by an actual
  need for multiple implementations *today*, not a hypothetical one later.
- **Prefer a plain function over a class when there's no state to hold.**
  Don't wrap stateless logic in a class "for consistency" if nothing else
  in the codebase needs that structure.
- **Prefer the standard library or an already-used dependency over adding a
  new package for a small piece of functionality.** Every new dependency is
  a maintenance cost — justify it.
- **Don't build configurability for options nobody asked for.** A function
  that takes 8 optional parameters "just in case" is harder to use and
  reason about than one that does one thing well. Add a parameter when a
  real caller needs it, not preemptively.
- **Flat is better than nested.** Avoid deep conditional nesting or deeply
  chained abstractions when an early return or a simpler control flow says
  the same thing more clearly.
- **If a simpler version of the solution exists that meets the actual
  requirement, ship the simpler version — even if the more complex one
  seems more "correct" in the abstract.** Correctness is measured against
  the actual requirement, not against an imagined ideal.

---

## 3. Match the Existing Codebase

- **Follow the patterns, naming conventions, and structure already
  established in this project.** Don't introduce a different style,
  folder layout, or naming scheme in one corner of the codebase because
  it's your personal preference — consistency across the codebase matters
  more than any individual file being "optimal."
- **Before adding a new file or module, check whether the functionality
  belongs in an existing one.** Don't fragment related logic across many
  tiny files when it reads better together, and don't cram unrelated logic
  into one file either — match the granularity the project already uses.
- **Read surrounding code before writing new code in the same area.** If
  the file uses a particular error-handling style, logging approach, or
  naming convention, match it rather than introducing a new one
  side-by-side.

---

## 4. Minimal, Reviewable Diffs

- **Change only what the task requires.** Don't reformat unrelated code,
  rename unrelated variables, or "clean up while you're in there" unless
  explicitly asked — unrelated changes make it hard to review what
  actually mattered for the task.
- **Don't refactor working code as a side effect of an unrelated feature
  request.** If a refactor is genuinely warranted, say so explicitly and
  do it as its own separate step, not folded silently into a feature
  change.
- **Keep functions and files reasonably sized.** If a function is doing
  several distinct things, split it — but don't split a short, cohesive
  function into multiple pieces purely to hit an arbitrary line count.

---

## 5. Naming & Readability

- **Names should say what something is or does, not how it's implemented.**
  `get_active_users()` not `filterUsersWhereActiveFlagTrue()`.
- **No abbreviations that aren't already standard in the codebase or
  language community.** Prefer clarity over saving keystrokes.
- **Avoid magic numbers and strings.** A repeated literal value (a limit, a
  status code, a key name) should be a named constant, defined once.
- **Comments explain *why*, not *what*.** Code should be readable enough
  that *what* it does is clear from reading it; comments are for
  non-obvious reasoning, trade-offs, or constraints that aren't visible in
  the code itself.

---

## 6. Error Handling — Real, Not Decorative

- **Don't wrap everything in a broad try/except that silently swallows
  errors.** Catch specific, expected failure modes and handle them
  meaningfully; let unexpected errors surface rather than hiding them
  behind a generic catch-all.
- **Fail loudly and early on missing configuration, invalid input, or
  broken assumptions** — don't let a function silently return `None` or an
  empty result when something actually went wrong.
- **Don't add error handling for failure modes that can't actually occur
  in context** — this is the same "unnecessary complexity" problem in a
  different shape.

---

## 7. Dependencies & Scope

- **Don't add a library for something a few lines of standard code can do.**
- **Don't scaffold generic, reusable infrastructure for a one-off task.**
  Build what's needed for the actual use case; generalize later if a
  second real use case actually shows up.
- **Stay inside the scope of the task you were given.** If you notice an
  unrelated improvement worth making, mention it — don't silently expand
  the task to include it.

---

## 8. When Something Seems Ambiguous

- **If a requirement is genuinely unclear or could be reasonably solved two
  different ways, pick the simpler one and note the assumption** — don't
  build both, don't build a configurable version that supports either, and
  don't invent extra scope to "cover all bases."
- **Don't add speculative flexibility to avoid asking a clarifying
  question.** If something is genuinely blocking, ask; otherwise, make the
  simplest reasonable choice and move forward.

---

## 9. Testing Discipline (when tests are in scope)

- **Test the actual behavior/contract of the code, not implementation
  details** — tests shouldn't break every time an internal detail changes
  if the external behavior hasn't.
- **Don't write a large volume of trivial tests to inflate coverage.** A
  few well-chosen tests covering real behavior and real edge cases beat
  many shallow ones.
- **Don't mock what you don't need to mock.** Prefer testing real logic
  directly; reserve mocks for genuine external dependencies (network,
  third-party APIs, time).

---

## 10. Before Finishing Any Task

Run this checklist against your own output before considering it done:

- [ ] Does this duplicate logic that already exists elsewhere in the repo?
- [ ] Did I introduce any abstraction, pattern, or config option that
      nothing in the current requirement actually needs?
- [ ] Could this be done with fewer moving parts (fewer files, fewer
      functions, fewer dependencies) without losing correctness or clarity?
- [ ] Does this match the existing codebase's style and structure?
- [ ] Did I change anything outside the actual scope of the task?
- [ ] Would a new engineer reading this understand it without needing me to
      explain it?

If any answer is concerning, simplify before calling the task complete —
don't ship the more complex version and mention the simpler alternative as
an aside.