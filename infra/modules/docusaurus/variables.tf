variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "bucket_name" {
  description = "S3 bucket name for Docusaurus static files"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name for Docusaurus site (e.g., docs.example.com)"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
}

variable "authentication_type" {
  description = "Authentication type: none, basic, cognito, or ip"
  type        = string
  default     = "none"

  validation {
    condition     = contains(["none", "basic", "cognito", "ip"], var.authentication_type)
    error_message = "authentication_type must be one of: none, basic, cognito, ip"
  }
}

variable "basic_auth_username" {
  description = "Username for Basic authentication (required if authentication_type = basic)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "basic_auth_password" {
  description = "Password for Basic authentication (required if authentication_type = basic)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "allowed_ip_ranges" {
  description = "List of allowed IP CIDR ranges for IP-based authentication (required if authentication_type = ip)"
  type        = list(string)
  default     = []
}

variable "cognito_user_pool_name" {
  description = "Cognito User Pool name for Docusaurus authentication"
  type        = string
  default     = "docusaurus-users"
}

variable "cognito_callback_urls" {
  description = "Cognito callback URLs"
  type        = list(string)
  default     = []
}

variable "cognito_logout_urls" {
  description = "Cognito logout URLs"
  type        = list(string)
  default     = []
}

variable "github_repository" {
  description = "GitHub repository in format 'org/repo' for OIDC authentication"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch for OIDC authentication"
  type        = string
  default     = "main"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
