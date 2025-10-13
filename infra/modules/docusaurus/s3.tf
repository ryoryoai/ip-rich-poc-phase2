# ============================================================================
# S3 Bucket for Docusaurus Static Files
# ============================================================================

resource "aws_s3_bucket" "docusaurus" {
  bucket = var.bucket_name

  tags = merge(var.tags, {
    Name = "${var.environment}-${var.project_name}-bucket"
    Type = "static-website"
  })
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "docusaurus" {
  bucket = aws_s3_bucket.docusaurus.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "docusaurus" {
  bucket = aws_s3_bucket.docusaurus.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket policy for CloudFront OAC
resource "aws_s3_bucket_policy" "docusaurus" {
  bucket     = aws_s3_bucket.docusaurus.id
  depends_on = [aws_s3_bucket_public_access_block.docusaurus]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.docusaurus.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.docusaurus.arn
          }
        }
      }
    ]
  })
}
