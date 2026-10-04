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

output "cloud_run_service_uri" {
  description = "HTTPS endpoint URI of the deployed Social Media Writer Agent."
  value       = google_cloud_run_v2_service.social_writer_agent.uri
}

output "agent_service_account_email" {
  description = "Least-privilege service account email used by the agent runtime."
  value       = google_service_account.agent_runtime_sa.email
}

output "telemetry_bigquery_dataset_id" {
  description = "BigQuery dataset ID receiving structured Intent-vs-Outcome audit logs."
  value       = google_bigquery_dataset.agent_telemetry_audit.dataset_id
}

output "managed_secret_ids" {
  description = "Secret Manager secret IDs mounted into the agent runtime."
  value = [
    google_secret_manager_secret.crm_mcp_token.secret_id,
    google_secret_manager_secret.marketing_db_credentials.secret_id,
    google_secret_manager_secret.social_perf_token.secret_id,
  ]
}
