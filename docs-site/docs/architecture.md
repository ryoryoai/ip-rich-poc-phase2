---
sidebar_position: 2
---

# AWS Infrastructure Architecture

This documentation site is hosted on AWS with a secure, scalable architecture featuring Cognito authentication.

## Architecture Overview

```plantuml AWS Infrastructure with Cognito
skinparam componentStyle rectangle
skinparam linetype ortho

actor User

rectangle "Security Layer" #FFE5E5 {
  component "AWS WAF" as waf <<Firewall>>
}

rectangle "CDN Layer" #E5F5FF {
  component "CloudFront" as cf <<CDN>>
}

rectangle "Authentication" #FFF5E5 {
  component "Cognito\nUser Pool" as cognito <<Auth>>
  component "Lambda@Edge" as lambda <<Function>>
}

rectangle "Storage" #E5FFE5 {
  component "S3 Bucket" as s3 <<Storage>>
}

User -down-> waf : HTTPS Request
waf -down-> cf : Filtered Traffic
cf -down-> lambda : Viewer Request
lambda -right-> cognito : Authenticate
cognito -down-> lambda : Token
lambda -down-> cf : Authorized
cf -down-> s3 : Origin Access\nControl (OAC)
s3 -up-> cf : HTML/JS/CSS
cf -up-> waf : Cached Content
waf -up-> User : Response

note right of cognito
  **Authentication:**
  - Email login
  - OAuth2/OIDC
  - Hosted UI
  - Password policy
  - MFA support
end note

note bottom of s3
  **Security:**
  - Private bucket
  - Versioning
  - Block public access
  - CloudFront OAC only
end note
```

## Key Components

### User Access Layer

- **Users**: Access the documentation site via web browser
- **HTTPS**: All traffic encrypted in transit

### Security Layer

- **AWS WAF**: Web Application Firewall protecting against common threats
  - SQL injection protection
  - XSS protection
  - Rate limiting
  - Geographic restrictions

### CDN Layer

- **CloudFront**: Global content delivery network
  - Edge caching for low latency
  - Custom domain support
  - SSL/TLS certificates
  - Lambda@Edge integration

### Authentication Layer (Optional)

- **Amazon Cognito**: User authentication and authorization
  - User Pool for user directory
  - OAuth2 / OpenID Connect support
  - Hosted UI for login/signup
  - Email verification
  - Password policies
- **Lambda@Edge**: Viewer request handler
  - Validates authentication tokens
  - Redirects to Cognito for login
  - Manages session cookies

### Storage Layer

- **S3 Bucket**: Static website hosting
  - Private bucket (not public)
  - Versioning enabled
  - Origin Access Control (OAC)
  - CloudFront-only access

## Request Flow

### Unauthenticated User (with Cognito)

1. User requests page → CloudFront
2. Lambda@Edge checks for auth token
3. No token → Redirect to Cognito Hosted UI
4. User logs in via Cognito
5. Cognito returns token
6. Lambda@Edge validates token
7. Request forwarded to S3
8. Content returned to user

### Authenticated User

1. User requests page with valid token
2. Lambda@Edge validates token
3. Request forwarded to S3 via CloudFront
4. S3 returns static content
5. CloudFront caches and delivers to user

### Public Access (without Cognito)

1. User requests page → CloudFront
2. CloudFront fetches from S3 (if not cached)
3. Content returned to user

## Security Features

- **Private S3 Bucket**: No public access, CloudFront only
- **Origin Access Control**: Secure communication between CloudFront and S3
- **WAF Protection**: Layer 7 DDoS protection and filtering
- **Cognito Authentication**: Optional user authentication
- **HTTPS Only**: Enforced encryption for all traffic
- **Versioning**: S3 object versioning for rollback capability

## Deployment

Infrastructure is managed with Terraform:

- `infra/environments/dev/`: Development environment
- `infra/modules/docusaurus/`: Reusable module
  - `s3.tf`: S3 bucket configuration
  - `cloudfront.tf`: CloudFront distribution
  - `cognito.tf`: Cognito authentication (optional)
  - `waf.tf`: WAF rules
  - `iam.tf`: IAM roles and policies
