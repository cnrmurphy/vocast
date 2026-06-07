# AGENTS.md

Guidance for AI agents working in this repository.

## Commit messages

Explain the **what** and the **why** in plain English — not a restatement of the diff.

- **Subject:** one concise line summarizing the change.
- **Body:** describe what changed and, more importantly, why — the problem it
  solves or the reasoning behind it. Write it so a reader understands the issue
  and the fix without reading the code.
- Include only necessary detail. Don't pad with obvious or redundant points.
- Skip the body entirely when the change is trivial and the subject says it all.

Favor clarity over completeness: a short message that explains the reasoning
beats a long one that lists every line touched.

## Tests

Test our own logic, not our dependencies. Assume third-party libraries and
tools work — don't write tests asserting that, say, ffmpeg produces a valid
file or a parser parses. Mock at the boundary and verify the behavior we
control (what we pass to a dependency, how we handle its result, how we
degrade when it fails).

Prefer self-documenting names over comments. A well-named variable or test
beats an inline comment explaining what the line does.
