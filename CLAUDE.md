# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An automated patent infringement investigation system with two main components:
1. **Documentation Site** (`docs-site/`): Docusaurus-based documentation with AWS CloudFront and flexible authentication (none, basic, Cognito, IP restriction)
2. **Patent Analysis App** (`apps/poc/phase1/`): Next.js app that automates patent infringement analysis using OpenAI Deep Research and web search APIs

## Key Commands

### Documentation Site (`docs-site/`)

```bash
cd docs-site
npm install              # Install dependencies
npm start                # Dev server on http://localhost:1919 (custom port!)
npm run build            # Production build
npm run serve            # Serve production build on http://localhost:1919
npm run typecheck        # TypeScript type checking
npm run format           # Format with Prettier
npm run format:check     # Check Prettier formatting

# PlantUML Diagrams
npm run diagrams:generate  # Generate all diagrams
npm run diagrams:current   # Generate current-workflow.svg
npm run diagrams:automated # Generate automated-workflow.svg
npm run diagrams:dataflow  # Generate data-flow.svg
```

### Patent Analysis App (`apps/poc/phase1/`)

```bash
cd apps/poc/phase1
npm install              # Install dependencies
npm run dev              # Dev server on http://localhost:3001 (custom port!)
npm run build            # Production build
npm start                # Production server (port 3002)
npm run lint             # ESLint check
npm run type-check       # TypeScript type check
npm run test             # Jest unit tests
npm run test:watch       # Jest watch mode
npm run test:e2e         # Playwright E2E tests
npm run test:e2e:ui      # Playwright UI mode
```

### Infrastructure (`infra/`)

Use mise for consistent Terraform (1.9.8) and Node.js (20) versions:

```bash
cd infra
mise trust              # Trust configuration
mise install            # Install tools
mise run lambda-install # Install Lambda@Edge dependencies (for Cognito auth)
mise run init           # terraform init
mise run plan           # terraform plan
mise run apply          # terraform apply
mise run validate       # terraform validate
mise run fmt            # terraform fmt
```

## Architecture

### Patent Analysis App Architecture

```
apps/poc/phase1/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analyze/start/     # Submit patent for async analysis
│   │   │   ├── analyze/status/    # Check job status
│   │   │   ├── analyze/result/    # Get completed results
│   │   │   ├── analyze/list/      # List all analysis jobs
│   │   │   ├── cron/check-and-do/ # Batch job processor (cron endpoint)
│   │   │   └── webhook/openai/    # OpenAI Deep Research webhook receiver
│   │   ├── research/              # Main UI (list, status, result pages)
│   │   └── simple/                # Simple analysis UI
│   ├── lib/
│   │   ├── container.ts           # DI container for providers
│   │   ├── prisma.ts              # Prisma client singleton
│   │   └── providers/             # LLM, Search, Patent providers
│   ├── services/                  # Core business logic
│   └── interfaces/                # Provider interfaces
└── prisma/schema.prisma           # Database schema
```

**Async Analysis Flow** (OpenAI Deep Research):
1. Client submits patent via `/api/analyze/start` → Job created with status `pending`
2. Cron (`/api/cron/check-and-do`) picks up pending jobs, calls OpenAI Deep Research API
3. Job status changes to `researching` while Deep Research runs (background: true)
4. Either cron polling or webhook (`/api/webhook/openai`) receives completion
5. Results stored in `analysis_jobs` table, status → `completed`

**Provider Pattern**: DI container (`lib/container.ts`) selects providers based on env vars:
- `LLM_PROVIDER`: `openai` | `claude`
- `SEARCH_PROVIDER`: `tavily` | `dummy`
- Patent provider: OpenAI Deep Research (default)

### Infrastructure Architecture

```
infra/
├── environments/dev/       # Environment-specific configs
│   └── main.tf            # Invokes docusaurus module
├── modules/docusaurus/     # Reusable Terraform module
│   ├── cloudfront.tf      # CDN + custom domain
│   ├── s3.tf              # Private static hosting bucket
│   ├── cognito.tf         # OAuth2 authentication (optional)
│   ├── waf.tf             # IP restriction (optional)
│   └── lambda/            # Lambda@Edge for Cognito auth
└── .mise.toml             # Tool version management
```

**Authentication Modes** (set in `terraform.tfvars`):
- `none`: Public access
- `basic`: CloudFront Functions single-user auth
- `cognito`: Lambda@Edge + Cognito OAuth2 multi-user
- `ip`: AWS WAF IP allowlist

## Important Notes

### Port Configuration
- **Docusaurus dev server**: Port **1919** (not 3000)
- **Patent app dev server**: Port **3001** (not 3000)
- **Patent app production**: Port **3002**

### PlantUML Workflow
1. Edit `.puml` files in `docs-site/docs/diagrams/`
2. Run `npm run diagrams:generate` to regenerate SVGs
3. Verify generated SVGs render correctly in Docusaurus

### Lambda@Edge Considerations
- Logs always in **us-east-1** CloudWatch (CloudFront requirement)
- Run `mise run lambda-install` before deploying Cognito auth
- Lambda function located in `infra/modules/docusaurus/lambda/`

### Environment Variables (Patent App)
```bash
# LLM Provider
LLM_PROVIDER=openai          # or "claude"
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Search Provider
SEARCH_PROVIDER=tavily        # or "dummy"
TAVILY_API_KEY=tvly-xxx

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://...   # Prisma Client (pgbouncer)
DIRECT_URL=postgresql://...     # Migrations (direct connection)

# OpenAI Deep Research (async processing)
OPENAI_DEEP_RESEARCH_MODEL=o4-mini-deep-research-2025-06-26
OPENAI_WEBHOOK_SECRET=whsec_xxx  # For webhook signature verification
CRON_SECRET_KEY=xxx              # Auth for cron endpoint

# Basic Auth (Vercel)
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure
SKIP_AUTH=false              # true only for development
```

### API Cost Considerations
- OpenAI Deep Research: Primary analysis method, usage-based pricing
- Claude API: ~$0.50 per 10 analyses (alternative provider)
- Tavily API: 1000 searches/month free

### Terraform State Operations
Per global CLAUDE.md: Avoid `terraform state rm/mv/import` without explicit user approval. Use standard Terraform workflow:
1. Modify `.tf` files
2. `mise run plan` to review changes
3. `mise run apply` after approval

### Deployment
- **Documentation Site**: GitHub Actions workflow (`deploy.yml`) deploys to S3+CloudFront
- **Patent App**: Vercel deployment via `vercel --prod` or GitHub integration

### Local Webhook Testing (ngrok)
For testing OpenAI Deep Research webhooks locally:
1. Start ngrok: `ngrok http 3001`
2. Update `OPENAI_WEBHOOK_URL` in `.env.local` with ngrok URL
3. Configure webhook URL in OpenAI Dashboard (https://platform.openai.com/webhooks)
4. Health check endpoint: `/api/ngrok/health`

## Common Development Tasks

### Adding Documentation
1. Create/edit `.md` files in `docs-site/docs/`
2. Update `sidebars.ts` if adding new sections
3. Run `npm start` to preview on localhost:1919
4. Commit after verifying with `npm run build`

### Modifying Patent Analysis Logic
1. API endpoints in `apps/poc/phase1/src/app/api/`
2. Provider implementations in `src/lib/providers/`
3. Add/modify provider interfaces in `src/interfaces/`
4. Test locally with `npm run dev` on localhost:3001
5. Verify types with `npm run type-check`

### Updating Infrastructure
1. Modify Terraform in `infra/modules/docusaurus/` or `infra/environments/dev/`
2. Run `mise run fmt` to format
3. Run `mise run plan` to preview changes
4. Apply only after reviewing plan output

### Running Analysis Locally
1. Copy `.env.local.example` to `.env.local`
2. Add API keys (OpenAI required, Tavily optional)
3. Set up database connection (DATABASE_URL, DIRECT_URL)
4. `npm run dev` in `apps/poc/phase1/`
5. Access http://localhost:3001/research for main UI

### Triggering Batch Processing
The cron endpoint processes pending jobs:
```bash
curl -X POST http://localhost:3001/api/cron/check-and-do \
  -H "X-Cron-Secret: your-cron-secret-key"
```

### Database Migration (Prisma)
**IMPORTANT**: This project uses `prisma db push` instead of traditional migrations for schema changes.

#### Production Database Changes
```bash
# 1. Pull production environment variables from Vercel
cd apps/poc/phase1
vercel env pull .env.production.local --environment production

# 2. Fix DIRECT_URL to include schema parameter
# Edit .env.production.local and ensure DIRECT_URL has ?schema=production

# 3. Push schema changes to production database
DATABASE_URL="<production_url>" DIRECT_URL="<direct_url>?schema=production" npx prisma db push
```

#### Local Development Database Changes
```bash
# Use the local schema
cd apps/poc/phase1
npx prisma db push
```

**Note**:
- Always use `prisma db push` for schema changes, not `prisma migrate dev`
- Production uses schema=production, local development uses schema=local
- Ensure DIRECT_URL includes the appropriate schema parameter