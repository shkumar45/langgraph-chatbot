terraform {
  required_version = ">= 1.5"

 backend "local" {
    path = "state/terraform.tfstate"
  }
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}