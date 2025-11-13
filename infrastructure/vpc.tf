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

# Create private subnets for RDS and ECS
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = data.aws_vpc.default.id
  cidr_block        = cidrsubnet(data.aws_vpc.default.cidr_block, 4, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
    Type = "Private"
  }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count  = 2
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip-${count.index + 1}"
  }

  depends_on = [data.aws_internet_gateway.default]
}

# NAT Gateways (one per AZ for high availability)
resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = count.index == 0 ? data.aws_subnet.default_az1.id : data.aws_subnet.default_az2.id

  tags = {
    Name = "${var.project_name}-nat-${count.index + 1}"
  }

  depends_on = [data.aws_internet_gateway.default]
}

# Default VPC already has a route table for public subnets, so we don't need to create one

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count  = 2
  vpc_id = data.aws_vpc.default.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.project_name}-private-rt-${count.index + 1}"
  }
}

# Route Table Associations for Private Subnets
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
