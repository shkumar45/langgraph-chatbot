resource "kubernetes_persistent_volume_claim_v1" "api_data" {
  metadata {
    name      = "api-data"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "standard"

    resources {
      requests = {
        storage = var.api_storage_size
      }
    }
  }
}