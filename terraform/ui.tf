resource "kubernetes_deployment_v1" "ui" {
  metadata {
    name      = "ui"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
    labels    = { app = "ui" }
  }

  spec {
    # Streamlit keeps each session in pod memory; >1 replica would need
    # sticky sessions.
    replicas = 1

    selector {
      match_labels = { app = "ui" }
    }

    template {
      metadata {
        labels = { app = "ui" }
      }

      spec {
        container {
          name              = "ui"
          image             = var.ui_image
          image_pull_policy = "IfNotPresent"

          port {
            name           = "http"
            container_port = 3000
          }

          env {
            name  = "API_BASE_URL"
            value = "http://${kubernetes_service_v1.api.metadata[0].name}:8000"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              memory = "512Mi"
            }
          }

          readiness_probe {
            http_get {
              path = "/_stcore/health"
              port = "http"
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }

          liveness_probe {
            http_get {
              path = "/_stcore/health"
              port = "http"
            }
            initial_delay_seconds = 15
            period_seconds        = 20
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "ui" {
  metadata {
    name      = "ui"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
  }

  spec {
    type     = "NodePort"
    selector = { app = "ui" }

    port {
      name        = "http"
      port        = 3000
      target_port = "http"
      node_port   = var.ui_node_port
    }
  }
}