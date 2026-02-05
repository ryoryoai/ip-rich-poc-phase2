# AGENTS.md

## Review guidelines
- Prioritize correctness, security, data loss risk, privacy, and cost regressions.
- Call out breaking changes to APIs, database schema, auth, cron, and webhooks.
- This repo uses the production DB for dev/test. Flag any destructive DB operations and require explicit approval before they run.
- Prisma policy: prefer `prisma db push`, avoid `prisma migrate dev`.
- Verify environment variables are validated and secrets are not logged.
- Require tests or rationale when behavior changes; mention missing coverage.
