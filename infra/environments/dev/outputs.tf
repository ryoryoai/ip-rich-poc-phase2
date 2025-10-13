# ============================================================================
# Dev Environment Outputs
# ============================================================================

output "s3_bucket_name" {
  description = "Name of the S3 bucket for Docusaurus files"
  value       = module.docusaurus.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.docusaurus.s3_bucket_arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = module.docusaurus.cloudfront_distribution_id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = module.docusaurus.cloudfront_distribution_arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.docusaurus.cloudfront_domain_name
}

output "custom_domain_name" {
  description = "Custom domain name for Docusaurus site"
  value       = module.docusaurus.custom_domain_name
}

output "website_url" {
  description = "URL to access the Docusaurus site"
  value       = module.docusaurus.website_url
}

output "authentication_type" {
  description = "Configured authentication type"
  value       = module.docusaurus.authentication_type
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool (if enabled)"
  value       = module.docusaurus.cognito_user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client (if enabled)"
  value       = module.docusaurus.cognito_user_pool_client_id
}

output "cognito_domain" {
  description = "Cognito domain for authentication (if enabled)"
  value       = module.docusaurus.cognito_domain
}

output "cloudfront_function_arn" {
  description = "ARN of the CloudFront Function (if enabled)"
  value       = module.docusaurus.cloudfront_function_arn
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL (if enabled)"
  value       = module.docusaurus.waf_web_acl_id
}

output "github_actions_role_arn" {
  description = "IAM Role ARN for GitHub Actions deployment"
  value       = module.docusaurus.github_actions_role_arn
}
