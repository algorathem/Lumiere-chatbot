provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg-lumiere-prototype-v1" {
  name     = "rg-lumiere-prototype-v1"
  location = "southeastasia"
}

module "resource_group" {
  source = "./resource_group"

  resource_group_name = var.resource_group_name
  location = var.location
}

module "storage_account" {
  source = "./storage_account"

  depends_on = [module.resource_group]

  resource_group_name = var.resource_group_name
  location = var.location
  name = var.storage_account_name
  container_name = var.container_name
}
