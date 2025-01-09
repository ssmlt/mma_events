resource "aws_subnet" "mma_events_private_a" {
  vpc_id     = aws_vpc.mma_events.id
  cidr_block = "10.0.1.0/27"
  availability_zone = "us-west-2a"
  map_public_ip_on_launch = false

  tags = {
    Name = "mma-events-private-a",
    Type = "Private"
  }
}

resource "aws_subnet" "mma_events_private_b" {
  vpc_id     = aws_vpc.mma_events.id
  cidr_block = "10.0.1.32/27"
  availability_zone = "us-west-2b"
  map_public_ip_on_launch = false

  tags = {
    Name = "mma-events-private-b",
    Type = "Private"
  }
}

resource "aws_subnet" "mma_events_public_a" {
  vpc_id     = aws_vpc.mma_events.id
  cidr_block = "10.0.1.64/27"
  availability_zone = "us-west-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "mma-events-public-a",
    Type = "Public"
  }
}

resource "aws_subnet" "mma_events_public_b" {
  vpc_id     = aws_vpc.mma_events.id
  cidr_block = "10.0.1.96/27"
  availability_zone = "us-west-2b"
  map_public_ip_on_launch = true

  tags = {
    Name = "mma-events-public-b",
    Type = "Public"
  }
}