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

resource "google_service_account" "agent_runtime_sa" {
  account_id   = "${var.agent_service_name}-sa"
  display_name = "NovaPulse Social Media Writer Agent Runtime SA"
  description  = "Least-privilege service account for Vertex AI, Secret Manager, DLP, and Cloud Trace."
}

locals {
  agent_iam_roles = [
    "roles/aiplatform.user",
    "roles/dlp.user",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/discoveryengine.viewer",
  ]
}

resource "google_project_iam_member" "agent_least_privilege_roles" {
  for_each = toset(local.agent_iam_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_secret_manager_secret" "crm_mcp_token" {
  secret_id = "social-writer-crm-mcp-token"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

resource "google_secret_manager_secret" "marketing_db_credentials" {
  secret_id = "social-writer-marketing-db-credentials"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

resource "google_secret_manager_secret" "social_perf_token" {
  secret_id = "social-writer-social-perf-token"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

resource "google_secret_manager_secret_iam_member" "crm_secret_access" {
  secret_id = google_secret_manager_secret.crm_mcp_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "marketing_secret_access" {
  secret_id = google_secret_manager_secret.marketing_db_credentials.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "social_perf_secret_access" {
  secret_id = google_secret_manager_secret.social_perf_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runtime_sa.email}"
}
