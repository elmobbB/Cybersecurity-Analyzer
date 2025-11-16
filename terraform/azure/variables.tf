variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cyber-analyzer"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "cyber-analyzer-rg"
}

variable "azure_openai_key_gpt_5_nano" {
  description = "Azure OpenAI API key for the application"
  type        = string
  sensitive   = true
  default     = ""
}
variable "ai_foundry_endpoint_gpt_5_nano" {
  description = "Azure OpenAI endpoint for the application"
  type        = string
  sensitive   = true
  default     = ""
}
variable "azure_openai_api_version" {
  description = "Azure OpenAI API version for the application"
  type        = string
  sensitive   = true
  default     = ""
}

variable "semgrep_app_token" {
  description = "Semgrep app token for security scanning"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docker_image_tag" {
  description = "Tag for the Docker image"
  type        = string
  default     = "latest"
}