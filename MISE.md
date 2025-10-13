# mise Version Management Guide

This project uses [mise](https://mise.jdx.dev/) for managing tool versions (Terraform and Node.js).

## Why mise?

- **Consistent versions**: Ensure everyone uses the same Terraform 1.9.8 and Node.js 20
- **Automatic switching**: Automatically use correct versions when entering directories
- **Project isolation**: Different projects can use different versions
- **Built-in tasks**: Run common commands with `mise run <task>`

## Installation

### macOS/Linux
```bash
curl https://mise.run | sh
```

### Alternative: Homebrew (macOS)
```bash
brew install mise
```

### Shell Setup

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
eval "$(mise activate bash)"  # for bash
eval "$(mise activate zsh)"   # for zsh
```

## Quick Start

```bash
# 1. Clone and enter project
cd fullstack-docusaurus-cloudfront

# 2. Trust the mise configuration
mise trust

# 3. Install all tools (Terraform + Node.js)
mise install

# 4. Verify installation
mise list
# terraform 1.9.8
# node      20.18.0
```

## Configuration Files

### Root: `.mise.toml`
- Global tools for the entire project
- Terraform 1.9.8
- Node.js 20.18.0

### `infra/.mise.toml`
- Terraform-specific configuration
- Useful tasks for infrastructure management

### `docs-site/.mise.toml`
- Node.js-specific configuration
- Useful tasks for Docusaurus development

## Using mise Tasks

### Infrastructure Tasks (from `infra/` directory)

```bash
cd infra

# Initialize Terraform
mise run init

# Plan infrastructure changes
mise run plan

# Apply changes
mise run apply

# Format Terraform files
mise run fmt

# Install Lambda dependencies
mise run lambda-install
```

### Docusaurus Tasks (from `docs-site/` directory)

```bash
cd docs-site

# Install dependencies
mise run install

# Start development server
mise run dev

# Build for production
mise run build

# Type checking
mise run typecheck
```

## Using Tools Directly

mise ensures correct versions are used:

```bash
# Terraform (automatically uses 1.9.8)
cd infra/environments/dev
terraform init
terraform plan

# Node.js (automatically uses 20.18.0)
cd docs-site
npm install
npm start
```

## Explicit Execution with mise exec

Force use of mise-managed versions:

```bash
# Explicit Terraform execution
mise exec -- terraform init
mise exec -- terraform plan

# Explicit npm execution
mise exec -- npm install
mise exec -- npm run build
```

## Checking Current Versions

```bash
# Show all installed tools
mise list

# Show current directory's tool versions
mise current

# Show tool installation path
mise which terraform
mise which node
```

## Updating Tool Versions

Edit `.mise.toml` files and run:

```bash
mise install
```

Example:
```toml
[tools]
terraform = "1.10.0"  # Update to newer version
node = "22.0.0"       # Update to newer version
```

## Troubleshooting

### Tools not found
```bash
# Reinstall tools
mise install

# Check if mise is activated in shell
which mise
```

### Wrong version being used
```bash
# Check current versions
mise current

# Ensure you've trusted the config
mise trust

# Reload shell
exec $SHELL
```

### Task not found
```bash
# List all available tasks
mise tasks

# Run from correct directory
cd infra  # for infrastructure tasks
cd docs-site  # for docusaurus tasks
```

## Without mise

You can still use the project without mise by installing:
- Terraform 1.9.8 manually
- Node.js 20.18.0 manually

Just run commands directly without `mise run` or `mise exec`.

## References

- [mise Documentation](https://mise.jdx.dev/)
- [mise GitHub](https://github.com/jdx/mise)
- [Task Runner](https://mise.jdx.dev/tasks/)
