# PLC Coach - VPC and Network Infrastructure

# Use Default VPC
data "aws_vpc" "default" {
  default = true
}

# Use existing Internet Gateway from default VPC
data "aws_internet_gateway" "default" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Get default subnets (they're public by default)
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Use first 2 default subnets for ALB
data "aws_subnet" "default_az1" {
  id = data.aws_subnets.default.ids[0]
}

data "aws_subnet" "default_az2" {
  id = data.aws_subnets.default.ids[1]
}

# Using default VPC public subnets for everything (no NAT Gateway needed)
# This saves ~$70/month and is fine for development/testing
# For production, you'd want private subnets with NAT Gateways
