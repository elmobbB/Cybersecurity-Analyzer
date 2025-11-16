variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "cyber-analyzer"
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