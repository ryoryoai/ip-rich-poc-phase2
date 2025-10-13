# ============================================================================
# AWS WAF for IP-based Access Control
# ============================================================================

# IP Set for allowed IP ranges
resource "aws_wafv2_ip_set" "allowed_ips" {
  count              = var.authentication_type == "ip" ? 1 : 0
  provider           = aws.us_east_1
  name               = "${var.environment}-${var.project_name}-allowed-ips"
  description        = "Allowed IP ranges for ${var.environment} ${var.project_name}"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses          = var.allowed_ip_ranges

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-allowed-ips"
  })
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  count       = var.authentication_type == "ip" ? 1 : 0
  provider    = aws.us_east_1
  name        = "${var.environment}-${var.project_name}-waf"
  description = "WAF for IP-based access control"
  scope       = "CLOUDFRONT"

  default_action {
    block {}
  }

  rule {
    name     = "AllowListedIPs"
    priority = 1

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.allowed_ips[0].arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.environment}-${var.project_name}-allowed-ips"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.environment}-${var.project_name}-waf"
    sampled_requests_enabled   = true
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-waf"
  })
}
