# Copyright 2026 Rishabh Ginotra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.38"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  required_apis = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "dlp.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "artifactregistry.googleapis.com",
    "discoveryengine.googleapis.com",
    "bigquery.googleapis.com",
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each           = toset(local.required_apis)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = "${var.agent_service_name}-repo"
  description   = "Container registry for the NovaPulse Enterprise Social Media Writer Agent"
  format        = "DOCKER"
  depends_on    = [google_project_service.enabled_apis]
}

resource "google_storage_bucket" "brand_guidelines_bucket" {
  name                        = "${var.project_id}-${var.agent_service_name}-guidelines"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  depends_on                  = [google_project_service.enabled_apis]
}

resource "google_cloud_run_v2_service" "social_writer_agent" {
  name     = var.agent_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.agent_runtime_sa.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "FAST_MODEL_NAME"
        value = var.fast_model_name
      }
      env {
        name  = "REASONING_MODEL_NAME"
        value = var.reasoning_model_name
      }
      env {
        name  = "USE_GCP_SECRET_MANAGER"
        value = "true"
      }
      env {
        name  = "OTEL_TRACES_EXPORTER"
        value = "google_cloud_trace"
      }
      env {
        name  = "ENABLE_LIVE_CLOUD_TRACE"
        value = "true"
      }

      env {
        name = "CRM_MCP_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.crm_mcp_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MARKETING_DB_CREDENTIALS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.marketing_db_credentials.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SOCIAL_PERF_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.social_perf_token.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis,
    google_secret_manager_secret_iam_member.crm_secret_access,
    google_secret_manager_secret_iam_member.marketing_secret_access,
    google_secret_manager_secret_iam_member.social_perf_secret_access,
  ]
}
