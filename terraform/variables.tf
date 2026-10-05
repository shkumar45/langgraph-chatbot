variable "namespace" {
  description = "Kubernetes namespace for the chatbot"
  type        = string
  default     = "chatbot"
}
variable "env_file" {
  description = "Path to the .env holding API keys (unquoted KEY=value lines)"
  type        = string
  default     = "../.env"
}

variable "secret_keys" {
  description = "Keys from .env that go into the Kubernetes Secret"
  type        = list(string)
  default     = ["OPENAI_API_KEY", "LANGCHAIN_API_KEY", "ALPHAVANTAGE_API_KEY"]
}

variable "openai_model" {
  type    = string
  default = "gpt-4o-mini"
}

variable "api_storage_size" {
  description = "Size of the volume holding the SQLite chat history"
  type        = string
  default     = "1Gi"
}

variable "api_image" {
  description = "Backend image (already loaded into minikube)"
  type        = string
  default     = "skumar45/langgraph-chatbot-backend:latest"
}

variable "ui_image" {
  description = "Frontend image (already loaded into minikube)"
  type        = string
  default     = "skumar45/langgraph-chatbot-frontend:latest"
}

variable "ui_node_port" {
  description = "Fixed NodePort for the UI (30000-32767)"
  type        = number
  default     = 30080
}