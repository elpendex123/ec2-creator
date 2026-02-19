variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "ec2-provisioner-cluster"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "node_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t2.micro"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 2
}
