variable "resource_group_name" {
  description = "The name for the Azure resource group"
  type        = string
  default     = "rg-lumiere-prototype-v1"
}

variable "location" {
  description = "The Azure Region in which all resources should be provisioned"
  type        = string
  default     = "southeastasia"
}

variable "storage_account_name" {
  description = "The name of the storage account"
  type        = string
  default     = "stlumierev1"
}

variable "container_name" {
  description = "The name of the storage container"
  type        = string
  default     = "lumiere-prototype-data"
}
