# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An automated patent infringement investigation system with two main components:
1. **Documentation Site** (`docs-site/`): Docusaurus-based documentation with AWS CloudFront and flexible authentication (none, basic, Cognito, IP restriction)
2. **Patent Analysis App** (`apps/poc/phase1/`): Next.js PoC that automates patent infringement analysis using AI (Claude/GPT) and web search (Tavily)

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
npm start                # Production server (port 3001)
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
│   ├── app/              # Next.js App Router pages
│   │   ├── api/analyze   # Main analysis API endpoint
│   │   └── analyze/      # Analysis UI page
│   ├── services/         # Core business logic
│   │   ├── PatentInfringementAnalyzer.ts    # Main orchestrator
│   │   ├── RequirementExtractionService.ts  # Extract patent requirements
│   │   └── ComplianceCheckService.ts        # Check product compliance
│   └── interfaces/       # Provider interfaces (LLM, Search, Storage)
└── .env.local.example    # Environment variables template
```

**Key Services Flow**:
1. `PatentInfringementAnalyzer` orchestrates the entire analysis
2. `RequirementExtractionService` extracts structured requirements from patent claims
3. Search provider (Tavily/Dummy) finds product information
4. `ComplianceCheckService` evaluates each requirement against product specs
5. Results formatted as JSON with infringement probability score

**Provider Pattern**: Dependency injection allows swapping LLM (Claude/OpenAI) and search (Tavily/Dummy) providers via environment variables.

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
LLM_PROVIDER=claude          # or "openai"
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Search Provider
SEARCH_PROVIDER=tavily        # or "dummy"
TAVILY_API_KEY=tvly-xxx

# Optional Basic Auth (Vercel)
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure
SKIP_AUTH=false              # true only for development
```

### API Cost Considerations
- Claude API: ~$0.50 per 10 patent analyses (free tier: $5 credit)
- Tavily API: 1000 searches/month free (~200-300 analyses)
- OpenAI: Usage-based pricing as fallback

### Terraform State Operations
Per global CLAUDE.md: Avoid `terraform state rm/mv/import` without explicit user approval. Use standard Terraform workflow:
1. Modify `.tf` files
2. `mise run plan` to review changes
3. `mise run apply` after approval

### Deployment
- **Documentation Site**: GitHub Actions workflow (`deploy.yml`) deploys to S3+CloudFront
- **Patent App**: Vercel deployment via `vercel --prod` or GitHub integration

## Common Development Tasks

### Adding Documentation
1. Create/edit `.md` files in `docs-site/docs/`
2. Update `sidebars.ts` if adding new sections
3. Run `npm start` to preview on localhost:1919
4. Commit after verifying with `npm run build`

### Modifying Patent Analysis Logic
1. Core logic in `apps/poc/phase1/src/services/`
2. Add/modify provider interfaces in `src/interfaces/`
3. Test locally with `npm run dev` on localhost:3001
4. Verify types with `npm run type-check`

### Updating Infrastructure
1. Modify Terraform in `infra/modules/docusaurus/` or `infra/environments/dev/`
2. Run `mise run fmt` to format
3. Run `mise run plan` to preview changes
4. Apply only after reviewing plan output

### Running Analysis Locally
1. Copy `.env.local.example` to `.env.local`
2. Add API keys (Claude/OpenAI + Tavily)
3. `npm run dev` in `apps/poc/phase1/`
4. Access http://localhost:3001/analyze