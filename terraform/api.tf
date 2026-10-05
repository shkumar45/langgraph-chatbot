resource "kubernetes_deployment_v1" "api" {
  metadata {
    name      = "api"
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
    labels    = { app = "api" }
  }

  spec {
    replicas = 1

    # RWO volume + SQLite: stop the old pod before starting the new one.
    strategy {
      type = "Recreate"
    }

    selector {
      match_labels = { app = "api" }
    }

    template {
      metadata {
        labels = { app = "api" }
      }

      spec {
        container {
          name              = "api"
          image             = var.api_image
          image_pull_policy = "IfNotPresent" # use the image loaded into minikube

          port {
            name           = "http"
            container_port = 8000
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.api_config.metadata[0].name
            }
          }
                 env_from {
            secret_ref {
              name = kubernetes_secret_v1.api_keys.metadata[0].name
            }
          }

          volume_mount {
            name       = "data"
            mount_path = "/data"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              memory = "1536Mi"
            }
          }

          # Allow up to 60s for startup (MCP tool discovery can take 25s).
          startup_probe {
            http_get {
              path = "/health"
              port = "http"
            }
            period_seconds    = 5
            failure_threshold = 12
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = "http"
            }
            period_seconds = 10
          }

          liveness_probe {
            http_get {
                             path = "/health"
              port = "http"
            }
            period_seconds    = 20
            failure_threshold = 3
          }
        }

        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.api_data.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "api" {
  metadata {
    name      = "api" # the UI resolves http://api:8000 by this name
    namespace = kubernetes_namespace_v1.chatbot.metadata[0].name
  }

  spec {
    type     = "ClusterIP" # internal only
    selector = { app = "api" }

    port {
      name        = "http"
      port        = 8000
      target_port = "http"
    }
  }
}