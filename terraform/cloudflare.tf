provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

data "kubernetes_service" "frontend" {
  depends_on = [helm_release.mern_app]
  
  metadata {
    name      = "frontend"
    namespace = "sample-mern"
  }
}

data "kubernetes_service" "hello_service" {
  depends_on = [helm_release.mern_app]
  
  metadata {
    name      = "hello-service"
    namespace = "sample-mern"
  }
}

data "kubernetes_service" "profile_service" {
  depends_on = [helm_release.mern_app]
  
  metadata {
    name      = "profile-service"
    namespace = "sample-mern"
  }
}

resource "cloudflare_record" "frontend" {
  zone_id = var.cloudflare_zone_id
  name    = "app"
  value   = data.kubernetes_service.frontend.status.0.load_balancer.0.ingress.0.hostname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "api_hello" {
  zone_id = var.cloudflare_zone_id
  name    = "api-hello"
  value   = data.kubernetes_service.hello_service.status.0.load_balancer.0.ingress.0.hostname
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_record" "api_profile" {
  zone_id = var.cloudflare_zone_id
  name    = "api-profile"
  value   = data.kubernetes_service.profile_service.status.0.load_balancer.0.ingress.0.hostname
  type    = "CNAME"
  proxied = true
}

# Add CloudFlare variables
variable "cloudflare_api_token" {
  description = "CloudFlare API Token"
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "CloudFlare Zone ID"
}