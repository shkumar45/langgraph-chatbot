resource "kubernetes_namespace_v1" "chatbot" {
  metadata {
    name = var.namespace
    labels = {
      app = "langgraph-chatbot"
    }
  }
}