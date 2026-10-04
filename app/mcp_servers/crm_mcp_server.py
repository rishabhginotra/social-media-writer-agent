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

"""CRM Audience & Account Intelligence MCP Server.

Exposes enterprise CRM audience segments, pain points, buying triggers, and
anonymized customer success metrics via the Model Context Protocol (MCP).
Supports both stdio MCP transport (via `mcp.server.fastmcp.FastMCP` when installed)
and direct deterministic invocation for low-latency local/CI execution.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from app.observability import PiiRedactionEngine, start_linked_span

DEFAULT_CRM_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_db"
    / "crm_accounts_and_segments.json"
)


class CrmMcpServer:
    """MCP Server backed by the synthetic CRM Audience & Account database."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_CRM_DB_PATH
        self.pii_redactor = PiiRedactionEngine()
        self._data = self._load_database()

    def _load_database(self) -> dict[str, Any]:
        with open(self.db_path, encoding="utf-8") as f:
            return json.load(f)

    def list_audience_segments(self) -> list[str]:
        """Return all valid audience segment IDs in the CRM database."""
        return [
            seg["segment_id"] for seg in self._data.get("audience_segments", [])
        ]

    def query_audience_segment(
        self,
        audience_segment_id: str,
        include_win_metrics: bool = True,
    ) -> dict[str, Any]:
        """Query the CRM database for a specific target audience segment.

        All returned records are scrubbed through `PiiRedactionEngine` before
        leaving the MCP server boundary to guarantee zero customer PII leakage.
        """
        with start_linked_span(
            "mcp.crm_server.query_audience_segment",
            attributes={
                "mcp.server": "crm-audience-mcp",
                "crm.audience_segment_id": audience_segment_id,
                "crm.include_win_metrics": include_win_metrics,
            },
        ):
            normalized = audience_segment_id.strip().lower()
            segments = self._data.get("audience_segments", [])
            matched_segment: dict[str, Any] | None = None

            for seg in segments:
                if seg["segment_id"].lower() == normalized:
                    matched_segment = seg
                    break
                if normalized in seg["segment_name"].lower():
                    matched_segment = seg
                    break

            if matched_segment is None:
                valid_segments = self.list_audience_segments()
                raise KeyError(
                    f"Audience segment '{audience_segment_id}' was not found in the CRM MCP database. "
                    f"Valid audience_segment_id values are: {valid_segments}."
                )

            result = {
                "status": "success",
                "segment_id": matched_segment["segment_id"],
                "segment_name": matched_segment["segment_name"],
                "top_pain_points": matched_segment["top_pain_points"],
                "key_buying_triggers": matched_segment["key_buying_triggers"],
                "anonymized_win_metrics": (
                    matched_segment.get("anonymized_win_metrics", [])
                    if include_win_metrics
                    else []
                ),
                "decision_maker_priorities": matched_segment.get(
                    "decision_maker_priorities", []
                ),
                "llm_recovery_instructions": None,
            }
            return self.pii_redactor.redact_Data(result)


def get_crm_mcp_toolset_config() -> dict[str, Any]:
    """Return the ADK `McpToolset` stdio connection configuration for the CRM MCP server."""
    return {
        "server_name": "novapulse-crm-mcp-server",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.crm_mcp_server"],
        "description": "MCP stdio server providing enterprise CRM audience segments and anonymized win metrics.",
    }


def main() -> None:
    """Entrypoint for running the CRM MCP server over stdio."""
    server = CrmMcpServer()
    try:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("novapulse-crm-mcp-server")

        @mcp.tool(
            name="fetch_crm_audience_segment_insights",
            description="Retrieve enterprise CRM audience pain points, buying triggers, and anonymized win metrics.",
        )
        def _mcp_query_segment(
            audience_segment_id: str,
            include_win_metrics: bool = True,
        ) -> dict[str, Any]:
            return server.query_audience_segment(
                audience_segment_id=audience_segment_id,
                include_win_metrics=include_win_metrics,
            )

        mcp.run(transport="stdio")
    except ImportError:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            params = request.get("params", {})
            response = server.query_audience_segment(
                audience_segment_id=params.get(
                    "audience_segment_id", "enterprise_cto_vp_eng"
                ),
                include_win_metrics=params.get("include_win_metrics", True),
            )
            sys.stdout.write(json.dumps({"result": response}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
