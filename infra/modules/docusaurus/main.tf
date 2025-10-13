# ============================================================================
# Terraform Configuration
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">= 5.0"
      configuration_aliases = [aws.us_east_1]
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0"
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
