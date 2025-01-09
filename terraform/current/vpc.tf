resource "aws_vpc" "mma_events" {
  cidr_block       = "10.0.1.0/24"
  instance_tenancy = "default"

  tags = {
    Name = "mma-events"
  }
}
