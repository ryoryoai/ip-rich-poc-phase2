# ============================================================================
# CloudFront Functions for Basic Authentication
# ============================================================================

# CloudFront Function for Basic Auth
resource "aws_cloudfront_function" "basic_auth" {
  count   = var.authentication_type == "basic" ? 1 : 0
  name    = "${var.environment}-${var.project_name}-basic-auth"
  runtime = "cloudfront-js-2.0"
  comment = "Basic authentication for ${var.environment} ${var.project_name}"
  publish = true

  code = <<-EOT
function handler(event) {
    var request = event.request;
    var headers = request.headers;

    // Base64 encoded credentials
    var authString = 'Basic ${base64encode("${var.basic_auth_username}:${var.basic_auth_password}")}';

    // Check if Authorization header exists and matches
    if (typeof headers.authorization === 'undefined' ||
        headers.authorization.value !== authString) {
        return {
            statusCode: 401,
            statusDescription: 'Unauthorized',
            headers: {
                'www-authenticate': { value: 'Basic realm="Secure Area"' }
            }
        };
    }

    // Authentication successful, continue with request
    return request;
}
EOT
}
