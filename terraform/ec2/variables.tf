variable "name" {
  description = "Name of the EC2 instance"
  type        = string
}

variable "ami" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "Instance type (t2.micro, t3.micro)"
  type        = string
  default     = "t2.micro"
}

variable "storage_gb" {
  description = "Storage size in GB"
  type        = number
  default     = 8
}

variable "key_name" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
  default     = "my_ec2_keypair"
}
