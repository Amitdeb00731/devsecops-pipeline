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

  # PLANTED (Phase 4): the management port is open to the entire internet so the
  # infrastructure-as-code scan can be shown failing. The Phase 4 remediation
  # commit restricts this ingress to var.admin_cidr.
  ingress {
    description = "PLANTED: management port open to the entire internet."
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
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
