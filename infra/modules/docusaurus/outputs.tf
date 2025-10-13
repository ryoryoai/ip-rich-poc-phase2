output "s3_bucket_name" {
  description = "Name of the S3 bucket for Docusaurus files"
  value       = aws_s3_bucket.docusaurus.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.docusaurus.arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.docusaurus.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.docusaurus.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.docusaurus.domain_name
}

output "custom_domain_name" {
  description = "Custom domain name for Docusaurus site"
  value       = var.domain_name
}

output "website_url" {
  description = "URL to access the Docusaurus site"
  value       = "https://${var.domain_name}"
}

output "authentication_type" {
  description = "Configured authentication type"
  value       = var.authentication_type
}

output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool (if authentication_type = cognito)"
  value       = var.authentication_type == "cognito" ? aws_cognito_user_pool.docusaurus[0].id : null
}

output "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool (if authentication_type = cognito)"
  value       = var.authentication_type == "cognito" ? aws_cognito_user_pool.docusaurus[0].arn : null
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client (if authentication_type = cognito)"
  value       = var.authentication_type == "cognito" ? aws_cognito_user_pool_client.docusaurus[0].id : null
}

output "cognito_domain" {
  description = "Cognito domain for authentication (if authentication_type = cognito)"
  value       = var.authentication_type == "cognito" ? aws_cognito_user_pool_domain.docusaurus[0].domain : null
}

output "lambda_function_arn" {
  description = "ARN of the Lambda@Edge authentication function (if authentication_type = cognito)"
  value       = var.authentication_type == "cognito" ? aws_lambda_function.auth[0].arn : null
}

output "cloudfront_function_arn" {
  description = "ARN of the CloudFront Function (if authentication_type = basic)"
  value       = var.authentication_type == "basic" ? aws_cloudfront_function.basic_auth[0].arn : null
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL (if authentication_type = ip)"
  value       = var.authentication_type == "ip" ? aws_wafv2_web_acl.main[0].id : null
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL (if authentication_type = ip)"
  value       = var.authentication_type == "ip" ? aws_wafv2_web_acl.main[0].arn : null
}

output "github_actions_role_arn" {
  description = "IAM Role ARN for GitHub Actions deployment"
  value       = aws_iam_role.github_actions.arn
}
