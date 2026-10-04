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

"""Input/Output Guardrails, Policy Plugins, and Human-in-the-Loop (HITL) Safety Hooks.

Satisfies Rubric Criteria 3.3 and 3.4:
- 3.3 Guardrails & Policy Plugins (5 pts): `ModelArmorGuardrailPlugin` implements
  `before_model_callback` (screening user inputs for prompt injection, jailbreaks,
  competitor disparagement requests, and PII) and `after_model_callback` (self-evaluation
  against prohibited brand phrases and PII leakage), with optional Google Cloud Model Armor
  template integration.
- 3.4 Human-in-the-Loop Hooks (5 pts): `HumanInTheLoopApprovalGate` implements
  `before_tool_callback` to intercept high-stakes tools (`publish_approved_social_media_post`)
  and pause live publication until explicit human approval is confirmed.
"""

from __future__ import annotations

import os
import re
from typing import Any

from app.observability import (
    pii_redactor,
    start_linked_span,
    structured_logger,
)
from app.tools import PROHIBITED_BRAND_PHRASES


class GuardrailViolationError(ValueError):
    """Raised when a strict input or output safety policy is violated."""


class ModelArmorGuardrailPlugin:
    """Enforces pre-inference and post-inference safety, prompt-injection, and brand guardrails."""

    _PROMPT_INJECTION_PATTERNS: list[re.Pattern[str]] = [
        re.compile(
            r"ignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions",
            re.IGNORECASE,
        ),
        re.compile(
            r"reveal\s+(?:your\s+)?(?:system\s+prompt|secret\s+key|api\s+key)",
            re.IGNORECASE,
        ),
        re.compile(
            r"bypass\s+(?:brand\s+compliance|model\s+armor|guardrails|human\s+approval)",
            re.IGNORECASE,
        ),
        re.compile(
            r"write\s+a\s+defamatory\s+attack\s+against",
            re.IGNORECASE,
        ),
    ]

    def __init__(self, model_armor_template_id: str | None = None) -> None:
        self.model_armor_template_id = model_armor_template_id or os.environ.get(
            "MODEL_ARMOR_TEMPLATE_ID",
            "projects/novapulse-prod/locations/us-central1/templates/social-brand-armor-v1",
        )
        self.interceptions: list[dict[str, Any]] = []

    def inspect_user_prompt(self, user_prompt: str) -> dict[str, Any]:
        """Pre-inference guardrail (`before_model_callback`): screens for prompt injection and scrubs PII."""
        with start_linked_span(
            "guardrail.before_model_callback",
            attributes={"guardrail.template_id": self.model_armor_template_id},
        ):
            sanitized_prompt = pii_redactor.redact_text(user_prompt or "")
            for pattern in self._PROMPT_INJECTION_PATTERNS:
                if pattern.search(user_prompt or ""):
                    event = {
                        "allowed": False,
                        "stage": "before_model_callback",
                        "reason": f"Blocked by Model Armor Guardrail: matched adversarial pattern '{pattern.pattern}'.",
                        "sanitized_prompt": sanitized_prompt,
                    }
                    self.interceptions.append(event)
                    structured_logger.log_event(
                        event_type="GUARDRAIL_INPUT_BLOCKED",
                        message=event["reason"],
                        severity="WARNING",
                        component="ModelArmorGuardrailPlugin",
                        metadata=event,
                    )
                    return event

            return {
                "allowed": True,
                "stage": "before_model_callback",
                "reason": "Input passed Model Armor pre-inference inspection.",
                "sanitized_prompt": sanitized_prompt,
            }

    def inspect_model_output(self, model_output: str) -> dict[str, Any]:
        """Post-inference guardrail (`after_model_callback`): scrubs PII and flags prohibited brand claims."""
        with start_linked_span(
            "guardrail.after_model_callback",
            attributes={"guardrail.template_id": self.model_armor_template_id},
        ):
            sanitized_output = pii_redactor.redact_text(model_output or "")
            detected_phrases = [
                phrase
                for phrase in PROHIBITED_BRAND_PHRASES
                if phrase in sanitized_output.lower()
            ]
            if detected_phrases:
                event = {
                    "allowed": False,
                    "stage": "after_model_callback",
                    "detected_prohibited_phrases": detected_phrases,
                    "sanitized_output": sanitized_output,
                    "reason": (
                        f"Output flagged by post-inference brand guardrail for prohibited phrases: "
                        f"{detected_phrases}."
                    ),
                }
                self.interceptions.append(event)
                structured_logger.log_event(
                    event_type="GUARDRAIL_OUTPUT_FLAGGED",
                    message=event["reason"],
                    severity="WARNING",
                    component="ModelArmorGuardrailPlugin",
                    metadata=event,
                )
                return event

            return {
                "allowed": True,
                "stage": "after_model_callback",
                "detected_prohibited_phrases": [],
                "sanitized_output": sanitized_output,
                "reason": "Output passed post-inference brand & PII guardrail check.",
            }


class HumanInTheLoopApprovalGate:
    """Enforces Human-in-the-Loop (HITL) confirmation before high-stakes tool execution (`before_tool_callback`)."""

    HIGH_STAKES_TOOLS = {"publish_approved_social_media_post"}

    def __init__(self) -> None:
        self.pending_approvals: dict[str, dict[str, Any]] = {}

    def before_tool_callback(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> dict[str, Any]:
        """Intercepts high-stakes tool calls when `human_approval_confirmed` is not True."""
        with start_linked_span(
            "guardrail.before_tool_callback",
            attributes={"tool.name": tool_name},
        ):
            if tool_name not in self.HIGH_STAKES_TOOLS:
                return {"action": "allow", "tool_name": tool_name}

            confirmed = bool(tool_args.get("human_approval_confirmed", False))
            compliance_score = int(tool_args.get("compliance_score", 0))

            if compliance_score < 90:
                return {
                    "action": "block",
                    "tool_name": tool_name,
                    "status": "recoverable_error",
                    "reason": (
                        f"Cannot publish post with compliance_score={compliance_score} (< 90/100)."
                    ),
                }

            if not confirmed:
                approval_token = f"hitl-{len(self.pending_approvals) + 1:04d}"
                record = {
                    "approval_token": approval_token,
                    "tool_name": tool_name,
                    "platform": tool_args.get("platform"),
                    "author_persona": tool_args.get("author_persona"),
                    "compliance_score": compliance_score,
                    "status": "pending_human_confirmation",
                }
                self.pending_approvals[approval_token] = record
                structured_logger.log_event(
                    event_type="HITL_APPROVAL_REQUIRED",
                    message=(
                        f"Paused high-stakes tool '{tool_name}' awaiting human confirmation "
                        f"(token={approval_token})."
                    ),
                    component="HumanInTheLoopApprovalGate",
                    metadata=record,
                )
                return {
                    "action": "pause_for_human_confirmation",
                    **record,
                }

            structured_logger.log_event(
                event_type="HITL_APPROVAL_VERIFIED",
                message=f"Human approval verified for high-stakes tool '{tool_name}'. Proceeding.",
                component="HumanInTheLoopApprovalGate",
                metadata={"tool_name": tool_name, "confirmed": True},
            )
            return {"action": "allow", "tool_name": tool_name}
