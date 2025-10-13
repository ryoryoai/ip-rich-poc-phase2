# ============================================================================
# CloudFront Distribution
# ============================================================================

# Origin Access Control for S3
resource "aws_cloudfront_origin_access_control" "docusaurus" {
  name                              = "${var.environment}-${var.project_name}-oac"
  description                       = "OAC for ${var.environment} ${var.project_name} bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "docusaurus" {
  origin {
    domain_name              = aws_s3_bucket.docusaurus.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.docusaurus.id
    origin_id                = "S3-${var.bucket_name}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.domain_name]
  comment             = "${var.environment} ${var.project_name} Documentation Site"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.bucket_name}"

    forwarded_values {
      query_string = false
      headers      = ["CloudFront-Viewer-Country"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true

    # Lambda@Edge for Cognito authentication
    dynamic "lambda_function_association" {
      for_each = var.authentication_type == "cognito" ? [1] : []
      content {
        event_type   = "viewer-request"
        lambda_arn   = aws_lambda_function.auth[0].qualified_arn
        include_body = false
      }
    }

    # CloudFront Functions for Basic authentication
    dynamic "function_association" {
      for_each = var.authentication_type == "basic" ? [1] : []
      content {
        event_type   = "viewer-request"
        function_arn = aws_cloudfront_function.basic_auth[0].arn
      }
    }
  }

  # Cache behavior for static assets (long cache)
  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.bucket_name}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 86400
    default_ttl            = 31536000
    max_ttl                = 31536000
    compress               = true
  }

  # Custom error response for SPA routing
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.docusaurus.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # WAF for IP-based access control
  web_acl_id = var.authentication_type == "ip" ? aws_wafv2_web_acl.main[0].arn : null

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-cloudfront"
  })
}

# ============================================================================
# ACM Certificate for Custom Domain
# ============================================================================

# ACM Certificate (must be in us-east-1 for CloudFront)
resource "aws_acm_certificate" "docusaurus" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-certificate"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Route 53 records for ACM validation
resource "aws_route53_record" "docusaurus_validation" {
  for_each = {
    for dvo in aws_acm_certificate.docusaurus.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.hosted_zone_id
}

# ACM Certificate validation
resource "aws_acm_certificate_validation" "docusaurus" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.docusaurus.arn
  validation_record_fqdns = [for record in aws_route53_record.docusaurus_validation : record.fqdn]
}

# ============================================================================
# Route 53 Record for CloudFront
# ============================================================================

# Route 53 A record for CloudFront
resource "aws_route53_record" "docusaurus" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.docusaurus.domain_name
    zone_id                = aws_cloudfront_distribution.docusaurus.hosted_zone_id
    evaluate_target_health = false
  }
}
