# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docusaurus-based documentation site with AWS CloudFront distribution and flexible authentication options (none, basic, Cognito, IP restriction). Infrastructure is managed with Terraform modules.

## Development Commands

### Docusaurus Site (docs-site/)

```bash
cd docs-site
npm install              # Install dependencies
npm start                # Dev server on http://localhost:1919
npm run build            # Production build
npm run serve            # Serve production build on http://localhost:1919
npm run typecheck        # TypeScript type checking
npm run format           # Format with Prettier
npm run format:check     # Check Prettier formatting
```

### PlantUML Diagrams (docs-site/)

```bash
npm run diagrams:generate  # Generate all diagrams
npm run diagrams:current   # Generate current-workflow.svg
npm run diagrams:automated # Generate automated-workflow.svg
npm run diagrams:dataflow  # Generate data-flow.svg
```

PlantUML diagrams are in `docs-site/docs/diagrams/*.puml` and generated to `*.svg`.

### Terraform Infrastructure (infra/)

Use mise for consistent tooling (Terraform 1.9.8, Node.js 20):

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
mise run fmt-check      # terraform fmt -check
```

**Without mise:**
```bash
cd infra/environments/dev
terraform init
terraform plan
terraform apply
```

### Deployment

GitHub Actions auto-deploys on workflow_dispatch. Manual deployment via `deploy.yml` workflow requires:
- `AWS_ROLE_ARN`
- `AWS_S3_BUCKET`
- `AWS_CLOUDFRONT_DISTRIBUTION_ID`

## Architecture

### Directory Structure

```
infra/
  environments/dev/       # Dev environment Terraform configs
  modules/docusaurus/     # Reusable Docusaurus module
    cloudfront.tf         # CloudFront + ACM + Route53
    cloudfront_functions.tf # Basic auth
    cognito.tf            # Cognito + Lambda@Edge OAuth2
    waf.tf                # IP restriction
    s3.tf                 # S3 static hosting
    iam.tf                # GitHub Actions IAM
    lambda/               # Lambda@Edge function for Cognito
  tools/docs-site/        # Additional infrastructure tools
  .mise.toml              # Terraform tooling config

docs-site/
  docs/                   # Markdown documentation
  src/                    # React components and custom CSS
  static/                 # Static assets
  docusaurus.config.ts    # Docusaurus configuration
  package.json            # Node dependencies and scripts
```

### Authentication Modes

Configure via `infra/environments/dev/terraform.tfvars`:

1. **none**: Public access
2. **basic**: CloudFront Functions (single user)
3. **cognito**: Lambda@Edge + AWS Cognito OAuth2 (multi-user)
4. **ip**: AWS WAF IP allowlist

### Docusaurus Configuration

- **Port**: Dev server runs on 1919 (not default 3000)
- **Route**: Docs at root path (`routeBasePath: "/"`)
- **Plugins**: PlantUML (`@mstroppel/remark-local-plantuml`), Mermaid, rehype-raw
- **Excludes**: `docs/diagrams/README.md` from routing

## Important Notes

- Docusaurus dev/serve port is **1919**, not 3000
- Lambda@Edge logs are in **us-east-1** CloudWatch, regardless of deployment region
- PlantUML diagrams must be regenerated after editing `.puml` files
- S3 bucket is private; access only via CloudFront OAC
- When using Cognito auth, run `mise run lambda-install` before Terraform apply
- Terraform state operations (rm/mv/import) require user approval per global CLAUDE.md

## Common Tasks

### Adding Documentation

1. Create/edit `.md` files in `docs-site/docs/`
2. Update `docs-site/sidebars.ts` if needed
3. Run `npm start` to preview locally
4. Run `npm run build` to verify production build

### PlantUML Workflow

1. Edit `.puml` files in `docs-site/docs/diagrams/`
2. Run `npm run diagrams:generate` (or specific diagram command)
3. Verify generated `.svg` files render correctly in Docusaurus

### Updating Infrastructure

1. Modify Terraform files in `infra/modules/docusaurus/` or `infra/environments/dev/`
2. Run `mise run plan` to review changes
3. Run `mise run apply` after approval
4. Avoid destructive state operations without explicit user consent

### Deploying to AWS

1. Trigger GitHub Actions workflow (manual dispatch)
2. Or push changes to main branch (when auto-deploy enabled in `deploy.yml`)
3. Verify CloudFront cache invalidation completes
