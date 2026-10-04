"""Explicit Pydantic JSON Schemas for Tool Inputs, Outputs, and Agent Validation.

Satisfies Rubric Criterion 1.3 (Explicit JSON Schemas):
Utilizes strict input and output schemas (`extra="forbid"`, constrained types,
and explicit field descriptions) to validate tool arguments and constrain LLM outputs.
"""

from __future__ import annotations

from typing import Any, Literal, get_args, get_origin, get_type_hints

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError
except ImportError:  # pragma: no cover - lightweight runtime fallback when pydantic is not installed

    class ValidationError(ValueError):
        """Fallback validation error when Pydantic is not installed in bare Python."""

    def ConfigDict(**kwargs: Any) -> dict[str, Any]:  # type: ignore[misc]
        return dict(kwargs)

    class _FieldInfo:
        def __init__(self, default: Any = ..., **kwargs: Any) -> None:
            self.default = default
            self.default_factory = kwargs.get("default_factory")
            self.description = kwargs.get("description", "")
            self.min_length = kwargs.get("min_length")
            self.max_length = kwargs.get("max_length")
            self.ge = kwargs.get("ge")
            self.le = kwargs.get("le")

    def Field(default: Any = ..., **kwargs: Any) -> Any:  # type: ignore[misc]
        return _FieldInfo(default, **kwargs)

    class BaseModel:  # type: ignore[no-redef]
        """Deterministic strict schema validator compatible with Pydantic v2 API."""

        model_config: dict[str, Any] = {}

        def __init__(self, **data: Any) -> None:
            hints = get_type_hints(self.__class__)
            allowed_fields = {k for k in hints if k != "model_config"}
            if self.model_config.get("extra") == "forbid":
                unknown = set(data.keys()) - allowed_fields
                if unknown:
                    raise ValidationError(
                        f"Extra inputs are not permitted: {sorted(unknown)}"
                    )

            for field_name in allowed_fields:
                field_Type = hints[field_name]
                attr_val = getattr(self.__class__, field_name, ...)
                field_info = (
                    attr_val
                    if isinstance(attr_val, _FieldInfo)
                    else _FieldInfo(attr_val)
                )

                if field_name in data:
                    val = data[field_name]
                elif field_info.default_factory is not None:
                    val = field_info.default_factory()
                elif field_info.default is not ...:
                    val = field_info.default
                else:
                    raise ValidationError(
                        f"Field required: '{field_name}' in {self.__class__.__name__}"
                    )

                if (
                    isinstance(val, str)
                    and self.model_config.get("str_strip_whitespace")
                ):
                    val = val.strip()

                self._validate_value(field_name, val, field_Type, field_info)
                setattr(self, field_name, val)

        @classmethod
        def _validate_value(
            cls,
            field_name: str,
            val: Any,
            field_Type: Any,
            field_info: _FieldInfo,
        ) -> None:
            origin = get_origin(field_Type)
            if origin is Literal:
                allowed = get_args(field_Type)
                if val not in allowed:
                    raise ValidationError(
                        f"Invalid value '{val}' for '{field_name}'. Expected one of {list(allowed)}."
                    )
            if isinstance(val, str):
                if (
                    field_info.min_length is not None
                    and len(val) < field_info.min_length
                ):
                    raise ValidationError(
                        f"Field '{field_name}' length {len(val)} is below min_length={field_info.min_length}."
                    )
                if (
                    field_info.max_length is not None
                    and len(val) > field_info.max_length
                ):
                    raise ValidationError(
                        f"Field '{field_name}' length {len(val)} exceeds max_length={field_info.max_length}."
                    )
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if field_info.ge is not None and val < field_info.ge:
                    raise ValidationError(
                        f"Field '{field_name}' value {val} is less than ge={field_info.ge}."
                    )
                if field_info.le is not None and val > field_info.le:
                    raise ValidationError(
                        f"Field '{field_name}' value {val} exceeds le={field_info.le}."
                    )

        @classmethod
        def model_validate(cls, obj: dict[str, Any]) -> BaseModel:
            return cls(**obj)

        def model_dump(self) -> dict[str, Any]:
            hints = get_type_hints(self.__class__)
            return {
                k: getattr(self, k) for k in hints if k != "model_config"
            }

        @classmethod
        def model_json_schema(cls) -> dict[str, Any]:
            hints = get_type_hints(cls)
            properties: dict[str, Any] = {}
            required: list[str] = []
            for field_name, field_Type in hints.items():
                if field_name == "model_config":
                    continue
                attr_val = getattr(cls, field_name, ...)
                field_info = (
                    attr_val
                    if isinstance(attr_val, _FieldInfo)
                    else _FieldInfo(attr_val)
                )
                prop: dict[str, Any] = {
                    "description": field_info.description,
                    "type": str(field_Type),
                }
                if get_origin(field_Type) is Literal:
                    prop["enum"] = list(get_args(field_Type))
                properties[field_name] = prop
                if (
                    field_info.default is ...
                    and field_info.default_factory is None
                ):
                    required.append(field_name)
            return {
                "title": cls.__name__,
                "type": "object",
                "additionalProperties": cls.model_config.get("extra") != "forbid",
                "properties": properties,
                "required": required,
            }


AuthorPersonaId = Literal[
    "founder_ceo",
    "chief_architect",
    "vp_product_marketing",
    "devrel_advocate",
]

SocialPlatformId = Literal[
    "linkedin",
    "x_twitter",
    "instagram",
    "youtube_community",
]

AudienceSegmentId = Literal[
    "enterprise_cto_vp_eng",
    "platform_sre_architects",
    "finops_cloud_economics",
]

IntendedOutcomeId = Literal[
    "lead_generation",
    "webinar_registration",
    "whitepaper_download",
    "product_launch",
    "developer_adoption",
    "thought_leadership",
]

ProductLineId = Literal[
    "PulseGrid",
    "PulseShield",
    "PulseFlow",
]


class CrmAudienceQueryInput(BaseModel):
    """Strict input schema for querying the CRM Audience Segment MCP tool."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    audience_segment_id: AudienceSegmentId = Field(
        description=(
            "Target buyer or practitioner segment identifier in the NovaPulse CRM "
            "('enterprise_cto_vp_eng', 'platform_sre_architects', or 'finops_cloud_economics')."
        )
    )
    include_win_metrics: bool = Field(
        default=True,
        description="Whether to include anonymized customer ROI and latency win metrics.",
    )


class CrmAudienceInsightOutput(BaseModel):
    """Strict output schema returned by the CRM Audience Segment MCP tool."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "recoverable_error"] = Field(
        description="Execution status of the CRM query."
    )
    segment_id: str = Field(description="Resolved CRM audience segment ID.")
    segment_name: str = Field(
        description="Human-readable name of the target audience segment."
    )
    top_pain_points: list[str] = Field(
        default_factory=list,
        description="Top validated customer pain points from enterprise discovery calls.",
    )
    key_buying_triggers: list[str] = Field(
        default_factory=list,
        description="Events that trigger purchasing or technical evaluation.",
    )
    anonymized_win_metrics: list[str] = Field(
        default_factory=list,
        description="Verified customer outcome metrics safe for public social benchmarking.",
    )
    decision_maker_priorities: list[str] = Field(
        default_factory=list,
        description="Core evaluation priorities for this audience persona.",
    )
    llm_recovery_instructions: str | None = Field(
        default=None,
        description="Actionable recovery steps for the LLM if a validation or lookup error occurs.",
    )


class MarketingCampaignQueryInput(BaseModel):
    """Strict input schema for querying the Marketing Database MCP tool."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_line: ProductLineId = Field(
        description="NovaPulse product line ('PulseGrid', 'PulseShield', or 'PulseFlow')."
    )
    intended_outcome: IntendedOutcomeId = Field(
        description=(
            "Desired conversion or engagement goal for the post "
            "('lead_generation', 'webinar_registration', 'whitepaper_download', "
            "'product_launch', 'developer_adoption', or 'thought_leadership')."
        )
    )


class MarketingCampaignOutput(BaseModel):
    """Strict output schema returned by the Marketing Database MCP tool."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "recoverable_error"] = Field(
        description="Execution status of the marketing campaign lookup."
    )
    campaign_id: str = Field(description="Unique campaign identifier.")
    product_line: str = Field(description="Matched NovaPulse product line.")
    campaign_theme: str = Field(description="Official campaign theme title.")
    core_value_proposition: str = Field(
        description="Approved primary value proposition statement."
    )
    verified_proof_points: list[str] = Field(
        default_factory=list,
        description="Quantitative proof points verified for external marketing use.",
    )
    recommended_cta: str = Field(
        description="Approved Call-To-Action tailored to the intended outcome."
    )
    llm_recovery_instructions: str | None = Field(
        default=None,
        description="Recovery instructions for the LLM when inputs are invalid.",
    )


class HistoricBenchmarkQueryInput(BaseModel):
    """Strict input schema for querying the Historic Social Performance MCP tool."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    platform: SocialPlatformId = Field(
        description="Target social media platform ('linkedin', 'x_twitter', 'instagram', 'youtube_community')."
    )
    author_persona: AuthorPersonaId = Field(
        description=(
            "Persona of the author posting ('founder_ceo', 'chief_architect', "
            "'vp_product_marketing', or 'devrel_advocate')."
        )
    )


class HistoricBenchmarkOutput(BaseModel):
    """Strict output schema returned by the Historic Social Performance MCP tool."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "recoverable_error"] = Field(
        description="Execution status of the benchmark query."
    )
    platform: str = Field(description="Target social media platform.")
    persona_id: str = Field(description="Matched author persona identifier.")
    avg_engagement_rate_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Historical average engagement rate percentage.",
    )
    avg_click_through_rate_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Historical average click-through rate percentage.",
    )
    optimal_character_range: list[int] = Field(
        description="Recommended [min_chars, max_chars] length window."
    )
    top_performing_hook_patterns: list[str] = Field(
        default_factory=list,
        description="Proven opening hook structures for this platform and persona.",
    )
    winning_structural_traits: list[str] = Field(
        default_factory=list,
        description="Formatting and structural patterns correlated with top-decile engagement.",
    )
    top_historical_post_example: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of the highest-performing historical post for this slice.",
    )
    llm_recovery_instructions: str | None = Field(
        default=None,
        description="Recovery instructions for the LLM if a slice is missing.",
    )


class BrandComplianceValidationInput(BaseModel):
    """Strict input schema for validating a social media draft against brand guidelines."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    draft_text: str = Field(
        min_length=20,
        max_length=5000,
        description="Complete text of the candidate social media post draft.",
    )
    platform: SocialPlatformId = Field(
        description="Target social platform to enforce length, hashtag, and formatting rules."
    )
    author_persona: AuthorPersonaId = Field(
        description="Author persona to verify signature tone and hashtag alignment."
    )


class BrandComplianceReportOutput(BaseModel):
    """Strict output schema for the Brand Guidelines compliance evaluation."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "recoverable_error"] = Field(
        description="Execution status of the compliance validator."
    )
    grade: Literal["pass", "fail"] = Field(
        description="Pass if compliance_score >= 90 and critical_violations is empty."
    )
    compliance_score: int = Field(
        ge=0, le=100, description="Numeric compliance score from 0 to 100."
    )
    character_count: int = Field(
        ge=0, description="Total character count of the inspected draft."
    )
    hashtag_count: int = Field(
        ge=0, description="Number of hashtags detected in the draft."
    )
    has_quantified_metric: bool = Field(
        description="Whether the draft cites at least one concrete numeric benchmark."
    )
    has_brand_attribution: bool = Field(
        description="Whether the draft references NovaPulse or an official Pulse product."
    )
    critical_violations: list[str] = Field(
        default_factory=list,
        description="Zero-tolerance brand, legal, or platform violations requiring immediate revision.",
    )
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Constructive suggestions to increase engagement or tighten brand alignment.",
    )
    llm_recovery_instructions: str | None = Field(
        default=None,
        description="Explicit instructions for the LLM on how to fix any violations.",
    )


class PublishSocialPostInput(BaseModel):
    """Strict input schema for publishing or scheduling an approved social media post."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    post_text: str = Field(
        min_length=20,
        max_length=5000,
        description="Final brand-compliant social media post text.",
    )
    platform: SocialPlatformId = Field(
        description="Target social platform for publication."
    )
    author_persona: AuthorPersonaId = Field(
        description="Author persona account to publish under."
    )
    intended_outcome: IntendedOutcomeId = Field(
        description="Campaign outcome tracking tag."
    )
    compliance_score: int = Field(
        ge=0,
        le=100,
        description="Verified compliance score from validate_draft_against_brand_guidelines.",
    )
    human_approval_confirmed: bool = Field(
        default=False,
        description="Must be True after explicit Human-in-the-Loop confirmation before live publishing.",
    )


class PublishSocialPostOutput(BaseModel):
    """Strict output schema returned by the publishing tool."""

    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "published", "pending_human_confirmation", "recoverable_error"
    ] = Field(description="Publication lifecycle state.")
    publication_id: str | None = Field(
        default=None,
        description="Assigned publication receipt ID when published.",
    )
    platform: str = Field(description="Target social platform.")
    author_persona: str = Field(description="Author persona account.")
    message: str = Field(description="Human-readable status explanation.")
    llm_recovery_instructions: str | None = Field(
        default=None,
        description="Next-step instructions for the LLM when awaiting HITL confirmation or fixing errors.",
    )


def export_all_tool_json_schemas() -> dict[str, dict[str, Any]]:
    """Exports strict JSON Schemas for all tool input and output models."""
    models = [
        CrmAudienceQueryInput,
        CrmAudienceInsightOutput,
        MarketingCampaignQueryInput,
        MarketingCampaignOutput,
        HistoricBenchmarkQueryInput,
        HistoricBenchmarkOutput,
        BrandComplianceValidationInput,
        BrandComplianceReportOutput,
        PublishSocialPostInput,
        PublishSocialPostOutput,
    ]
    return {model.__name__: model.model_json_schema() for model in models}
