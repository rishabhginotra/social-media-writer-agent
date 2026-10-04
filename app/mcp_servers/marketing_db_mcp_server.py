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

"""Marketing Campaign & Messaging Database MCP Server.

Exposes active product positioning, verified technical proof points, approved
statistics, and outcome-aligned calls-to-action (CTAs) via the Model Context
Protocol (MCP).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from app.observability import PiiRedactionEngine, start_linked_span

DEFAULT_MARKETING_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_db"
    / "marketing_campaigns.json"
)


class MarketingDatabaseMcpServer:
    """MCP Server backed by the synthetic Marketing Campaign & Messaging database."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_MARKETING_DB_PATH
        self.pii_redactor = PiiRedactionEngine()
        self._data = self._load_database()

    def _load_database(self) -> dict[str, Any]:
        with open(self.db_path, encoding="utf-8") as f:
            return json.load(f)

    def list_product_lines(self) -> list[str]:
        """Return available product lines in the Marketing database."""
        return [
            c["product_line"] for c in self._data.get("campaigns", [])
        ]

    def query_campaign(
        self,
        product_line: str,
        intended_outcome: str,
    ) -> dict[str, Any]:
        """Query the Marketing Campaign database by product line and intended outcome."""
        with start_linked_span(
            "mcp.marketing_db_server.query_campaign",
            attributes={
                "mcp.server": "marketing-db-mcp",
                "marketing.product_line": product_line,
                "marketing.intended_outcome": intended_outcome,
            },
        ):
            campaigns = self._data.get("campaigns", [])
            product_norm = product_line.strip().lower()
            outcome_norm = intended_outcome.strip().lower()

            matched_campaign: dict[str, Any] | None = None
            for camp in campaigns:
                if camp.get("product_line", "").lower() == product_norm:
                    matched_campaign = camp
                    break

            if matched_campaign is None:
                valid_products = self.list_product_lines()
                raise KeyError(
                    f"Product line '{product_line}' was not found in the Marketing Campaign MCP database. "
                    f"Valid product_line values are: {valid_products}."
                )

            approved_ctas = matched_campaign.get("approved_ctas", {})
            recommended_cta = approved_ctas.get(
                outcome_norm,
                next(iter(approved_ctas.values()), ""),
            )

            response = {
                "status": "success",
                "campaign_id": matched_campaign["campaign_id"],
                "product_line": matched_campaign["product_line"],
                "campaign_theme": matched_campaign["campaign_theme"],
                "core_value_proposition": matched_campaign[
                    "core_value_proposition"
                ],
                "verified_proof_points": matched_campaign[
                    "verified_proof_points"
                ],
                "recommended_cta": recommended_cta,
                "llm_recovery_instructions": None,
            }
            return self.pii_redactor.redact_Data(response)


def get_marketing_mcp_toolset_config() -> dict[str, Any]:
    """Return the ADK `McpToolset` stdio connection configuration for the Marketing DB MCP server."""
    return {
        "server_name": "novapulse-marketing-db-mcp-server",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.marketing_db_mcp_server"],
        "description": "MCP stdio server providing verified marketing campaign value propositions, proof points, and CTAs.",
    }


def main() -> None:
    """Entrypoint for running the Marketing DB MCP server over stdio."""
    server = MarketingDatabaseMcpServer()
    try:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("novapulse-marketing-db-mcp-server")

        @mcp.tool(
            name="query_marketing_campaign_value_propositions",
            description="Query verified marketing campaign value propositions, proof points, and outcome-aligned CTAs.",
        )
        def _mcp_query_campaigns(
            product_line: str,
            intended_outcome: str = "thought_leadership",
        ) -> dict[str, Any]:
            return server.query_campaign(
                product_line=product_line,
                intended_outcome=intended_outcome,
            )

        mcp.run(transport="stdio")
    except ImportError:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            params = request.get("params", {})
            response = server.query_campaign(
                product_line=params.get("product_line", "PulseGrid"),
                intended_outcome=params.get(
                    "intended_outcome", "thought_leadership"
                ),
            )
            sys.stdout.write(json.dumps({"result": response}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
