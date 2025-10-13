# ============================================================================
# Docusaurus Module for Dev Environment
# ============================================================================

module "docusaurus" {
  source = "../../modules/docusaurus"

  # Environment Configuration
  environment  = var.environment
  project_name = var.project_name
  aws_region   = var.aws_region

  # S3 Configuration
  bucket_name = var.bucket_name

  # Domain Configuration
  domain_name    = var.domain_name
  hosted_zone_id = var.hosted_zone_id

  # Authentication Configuration
  authentication_type    = var.authentication_type
  basic_auth_username    = var.basic_auth_username
  basic_auth_password    = var.basic_auth_password
  allowed_ip_ranges      = var.allowed_ip_ranges
  cognito_user_pool_name = var.cognito_user_pool_name
  cognito_callback_urls  = var.cognito_callback_urls
  cognito_logout_urls    = var.cognito_logout_urls

  # GitHub OIDC Configuration
  github_repository = var.github_repository
  github_branch     = var.github_branch

  # Tags
  tags = var.tags

  # Pass providers to module
  providers = {
    aws.us_east_1 = aws.us_east_1
  }
}
