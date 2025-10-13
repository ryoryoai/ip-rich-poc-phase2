# ============================================================================
# Cognito User Pool (Optional)
# ============================================================================

resource "aws_cognito_user_pool" "docusaurus" {
  count = var.authentication_type == "cognito" ? 1 : 0
  name  = var.cognito_user_pool_name

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-user-pool"
  })
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "docusaurus" {
  count        = var.authentication_type == "cognito" ? 1 : 0
  name         = "${var.environment}-${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.docusaurus[0].id

  generate_secret = true

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  callback_urls = var.cognito_callback_urls
  logout_urls   = var.cognito_logout_urls

  supported_identity_providers = ["COGNITO"]

  access_token_validity  = 1  # 1 hour
  id_token_validity      = 1  # 1 hour
  refresh_token_validity = 30 # 30 days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "docusaurus" {
  count        = var.authentication_type == "cognito" ? 1 : 0
  domain       = "${var.environment}-${var.project_name}-auth"
  user_pool_id = aws_cognito_user_pool.docusaurus[0].id
}

# ============================================================================
# Lambda@Edge Function for Cognito Authentication (Optional)
# ============================================================================

# Lambda execution role
resource "aws_iam_role" "lambda_edge" {
  count = var.authentication_type == "cognito" ? 1 : 0
  name  = "${var.environment}-${var.project_name}-lambda-edge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = var.tags
}

# Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_edge_basic" {
  count      = var.authentication_type == "cognito" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_edge[0].name
}

# Lambda function package
resource "local_file" "lambda_config" {
  count = var.authentication_type == "cognito" ? 1 : 0
  content = templatefile("${path.module}/lambda/index.js", {
    USER_POOL_ID   = aws_cognito_user_pool.docusaurus[0].id
    CLIENT_ID      = aws_cognito_user_pool_client.docusaurus[0].id
    CLIENT_SECRET  = aws_cognito_user_pool_client.docusaurus[0].client_secret
    COGNITO_DOMAIN = aws_cognito_user_pool_domain.docusaurus[0].domain
    REGION         = data.aws_region.current.id
  })
  filename = "${path.module}/lambda_build/index.js"
}

resource "null_resource" "lambda_prep" {
  count      = var.authentication_type == "cognito" ? 1 : 0
  depends_on = [local_file.lambda_config]

  provisioner "local-exec" {
    command = <<-EOT
      cp -r ${path.module}/lambda/package.json ${path.module}/lambda_build/
      cd ${path.module}/lambda_build && npm install --production
    EOT
  }

  triggers = {
    always_run = timestamp()
  }
}

data "archive_file" "lambda_edge" {
  count       = var.authentication_type == "cognito" ? 1 : 0
  type        = "zip"
  source_dir  = "${path.module}/lambda_build"
  output_path = "${path.module}/lambda_function.zip"

  depends_on = [null_resource.lambda_prep]
}

# Lambda function (must be in us-east-1 for CloudFront)
resource "aws_lambda_function" "auth" {
  count            = var.authentication_type == "cognito" ? 1 : 0
  provider         = aws.us_east_1
  filename         = data.archive_file.lambda_edge[0].output_path
  function_name    = "${var.environment}-${var.project_name}-auth"
  role             = aws_iam_role.lambda_edge[0].arn
  handler          = "index.handler"
  source_code_hash = data.archive_file.lambda_edge[0].output_base64sha256
  runtime          = "nodejs20.x"
  timeout          = 5
  publish          = true

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-auth-lambda"
  })
}
