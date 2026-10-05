locals {
  # Parse .env: keep KEY=value lines, skip comments/blanks, split on the first "=".
  env_lines = [
    for line in split("\n", file(var.env_file)) : trimspace(line)
    if can(regex("^[A-Za-z_][A-Za-z0-9_]*=", trimspace(line)))
  ]
  dotenv = {
    for line in local.env_lines :
    split("=", line)[0] => join("=", slice(split("=", line), 1, length(split("=", line))))
  }
}

resource "kubernetes_secret_v1" "api_keys" {
  metadata {
    name      = "chatbot-api-keys"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
  }

  # The provider base64-encodes these for you.
  data = { for k in var.secret_keys : k => local.dotenv[k] }
}

resource "kubernetes_config_map_v1" "api_config" {
  metadata {
    name      = "chatbot-api-config"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
  }

  data = {
    OPENAI_MODEL         = var.openai_model
    LANGCHAIN_TRACING_V2 = "true"
    LANGCHAIN_ENDPOINT   = "https://api.smith.langchain.com"
    LANGCHAIN_PROJECT    = "langgraph-chatbot-project"
    CHECKPOINTER         = "sqlite"
    CHECKPOINT_DB        = "/data/chatbot.db"
    API_HOST             = "0.0.0.0"
    API_PORT             = "8000"
  }
}