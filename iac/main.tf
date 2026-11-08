terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for the lab resources."
  type        = string
  default     = "eu-north-1"
}

variable "admin_cidr" {
  description = "The single trusted CIDR allowed to reach the management port. Never 0.0.0.0/0."
  type        = string
  default     = "10.0.0.0/32"
}

variable "vpc_id" {
  description = "The VPC the security group is created in."
  type        = string
  default     = "vpc-0123456789abcdef0"
}

resource "aws_security_group" "app" {
  #checkov:skip=CKV2_AWS_5:Illustrative security group for the scan; not attached to a running instance in this cost-free lab.
  name        = "vulnerable-bank-api-sg"
  description = "Security group for the vulnerable-bank-api service, management access restricted to the trusted admin CIDR."
  vpc_id      = var.vpc_id

  # Remediated (Phase 4 IaC scan): management access is restricted to the single
  # trusted admin CIDR instead of the entire internet.
  ingress {
    description = "Management access from the trusted admin network only."
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "Outbound HTTPS to reach package and update endpoints."
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "vulnerable-bank-api-sg"
  }
}
