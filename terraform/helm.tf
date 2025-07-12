provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
      command     = "aws"
    }
  }
}

resource "kubernetes_namespace" "mern_app" {
  metadata {
    name = "sample-mern"
  }
}

resource "kubernetes_secret" "ecr_registry_secret" {
  metadata {
    name      = "ecr-registry-secret"
    namespace = kubernetes_namespace.mern_app.metadata[0].name
  }

  type = "kubernetes.io/dockerconfigjson"

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "${replace(aws_ecr_repository.frontend.repository_url, "/\\/.*$/", "")}" = {
          "username" = "AWS"
          "password" = data.aws_ecr_authorization_token.token.password
          "email"    = "no-reply@example.com"
          "auth"     = base64encode("AWS:${data.aws_ecr_authorization_token.token.password}")
        }
      }
    })
  }
}

data "aws_ecr_authorization_token" "token" {}

resource "helm_release" "mern_app" {
  name       = "mern-app"
  chart      = "../mern-app"
  namespace  = kubernetes_namespace.mern_app.metadata[0].name
  depends_on = [
    kubernetes_secret.ecr_registry_secret
  ]

  set {
    name  = "global.environment"
    value = "eks"
  }

  set {
    name  = "global.registry.eks.url"
    value = replace(aws_ecr_repository.frontend.repository_url, "/\\/.*$/", "")
  }
}