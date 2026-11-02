\# AEGIS — Engineering Rules



\## 1. Core Principle

Build secure, reliable and maintainable software with the least necessary complexity.



Do not write code merely to increase implementation size. Every line must have a clear purpose.



\## 2. Question Every Line

Before adding or modifying code, ask:



\- Is this line necessary?

\- Can existing functionality perform this task?

\- Is this logic already implemented elsewhere?

\- Can the solution be simpler without losing readability?

\- Does this introduce unnecessary complexity?



Remove unnecessary code.



\## 3. Code Reusability

\- Inspect existing modules before implementing new functionality.

\- Reuse existing functions, classes and utilities where appropriate.

\- Avoid duplicate business logic.

\- Extract shared logic when it genuinely benefits multiple components.

\- Do not create abstractions for trivial one-time operations.



\## 4. Code Quality

\- Prefer readable, maintainable code over clever shortcuts.

\- Use meaningful names.

\- Keep functions focused and reasonably small.

\- Avoid unnecessary comments and excessive nesting.

\- Remove unused imports, variables and unreachable code.

\- Avoid unnecessary dependencies.



\## 5. Security

\- Validate untrusted inputs.

\- Apply least-privilege principles.

\- Never hardcode credentials or secrets.

\- Handle errors safely.

\- Never bypass AEGIS authorization or policy checks for convenience.



\## 6. Testing

\- Run relevant tests after modifications.

\- Add tests for new functionality.

\- Check existing functionality for regressions.

\- Never claim tests passed unless they were actually executed.

\- Never hide failing tests.



\## 7. Before Completing a Task

Review the changes and report:



1\. Files created or modified.

2\. Unnecessary code removed.

3\. Duplicate logic identified or eliminated.

4\. Existing components reused.

5\. Tests executed and their actual results.

6\. Security concerns.

7\. Remaining issues or limitations.



\## 8. Restrictions

\- Do not rewrite working modules without a valid reason.

\- Do not add dependencies without explaining why.

\- Do not delete user data or make destructive changes without approval.

\- Do not silently change existing behavior.

\- Do not claim that an independent GPT review has happened unless it actually has.



\## 9. Final Quality Gate

Before declaring a task complete, inspect every changed line.



The goal is not the fewest possible lines. The goal is the simplest correct, secure and maintainable implementation.

