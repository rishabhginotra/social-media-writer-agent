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

resource "google_bigquery_dataset" "agent_telemetry_audit" {
  dataset_id  = "social_writer_agent_telemetry_${var.environment}"
  location    = var.region
  description = "Stores structured JSON logs, Intent-vs-Outcome audits, and brand compliance metrics."
  depends_on  = [google_project_service.enabled_apis]
}

resource "google_logging_project_sink" "intent_outcome_audit_sink" {
  name                   = "${var.agent_service_name}-audit-sink"
  destination            = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.agent_telemetry_audit.dataset_id}"
  filter                 = "jsonPayload.component=\"NovaPulseSocialMediaWriterCoordinator\" OR jsonPayload.event_type=\"INTENT_DECLARED\" OR jsonPayload.event_type=\"OUTCOME_RECORDED\""
  unique_writer_identity = true
}

resource "google_bigquery_dataset_iam_member" "log_sink_bq_writer" {
  dataset_id = google_bigquery_dataset.agent_telemetry_audit.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.intent_outcome_audit_sink.writer_identity
}
