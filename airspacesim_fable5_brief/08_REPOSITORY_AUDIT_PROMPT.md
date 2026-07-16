# Repository audit prompt

Before changing code, inspect the entire repository and report:

1. Repository tree.
2. Frontend entry points and routes.
3. Backend entry points and APIs.
4. Current location of simulation logic.
5. Current scenario definitions.
6. Current lesson content.
7. Current separation logic.
8. Current Practice evaluation logic.
9. Current Simulate summary logic.
10. Gao-specific or sensitive-looking public data.
11. Hard-coded callsigns, routes, fixes, levels, coordinates, scenario IDs, commands, texts, and rules.
12. Duplicate simulation logic.
13. Existing tests and gaps.
14. Current database state.
15. Current authentication state.
16. Current i18n state.
17. Current deployment configuration.
18. Risks in extracting the engine.
19. Reusable code to preserve.
20. A phased migration plan mapped to the brief.

Classify each finding as:

- keep;
- move;
- refactor;
- replace;
- remove;
- investigate.

Do not modify code during the audit. Do not recommend a full rewrite without concrete evidence.
