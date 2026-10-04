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

variable "project_id" {
  description = "Google Cloud Project ID hosting the Social Media Writer Agent."
  type        = str
}

variable "region" {
  description = "Primary GCP region for Cloud Run, Vertex AI, and Secret Manager."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment label (development, staging, production)."
  type        = string
  default     = "production"
}

variable "agent_service_name" {
  description = "Cloud Run / Vertex AI Agent Engine service identifier."
  type        = string
  default     = "social-media-writer-agent"
}

variable "container_image" {
  description = "Artifact Registry container image URI for the agent service."
  type        = string
  default     = "us-central1-docker.pkg.dev/novapulse-agent-demo/social-media-writer-agent-repo/agent:latest"
}

variable "fast_model_name" {
  description = "Low-latency Gemini model used for MCP lookups and compliance scoring."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "reasoning_model_name" {
  description = "High-reasoning Gemini model used for persona copywriting and remediation."
  type        = string
  default     = "gemini-2.5-pro"
}

variable "min_instances" {
  description = "Minimum warm Cloud Run instances."
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum autoscaled Cloud Run instances."
  type        = number
  default     = 10
}
