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

"""Historic Social Media Performance Benchmark MCP Server.

Exposes historical social media analytics, top-performing structural patterns,
engagement rates, click-through rates (CTR), and exemplar posts across platforms
(`linkedin`, `x_twitter`, `instagram`, `youtube_community`) and author personas
via the Model Context Protocol (MCP).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from app.observability import PiiRedactionEngine, start_linked_span

DEFAULT_SOCIAL_PERF_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_db"
    / "historic_social_performance.json"
)


class SocialPerformanceMcpServer:
    """MCP Server backed by the synthetic Historic Social Media Performance database."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_SOCIAL_PERF_DB_PATH
        self.pii_redactor = PiiRedactionEngine()
        self._data = self._load_database()

    def _load_database(self) -> dict[str, Any]:
        with open(self.db_path, encoding="utf-8") as f:
            return json.load(f)

    def query_benchmarks(
        self,
        platform: str,
        author_persona: str,
    ) -> dict[str, Any]:
        """Retrieve historical social media benchmarks and top-performing exemplars."""
        with start_linked_span(
            "mcp.social_performance_server.query_benchmarks",
            attributes={
                "mcp.server": "social-performance-mcp",
                "social.platform": platform,
                "social.author_persona": author_persona,
            },
        ):
            platform_norm = platform.strip().lower()
            persona_norm = author_persona.strip().lower()

            slices = self._data.get("platform_benchmarks", [])
            exact_match: dict[str, Any] | None = None
            platform_fallback: dict[str, Any] | None = None

            for entry in slices:
                if entry.get("platform") == platform_norm:
                    if platform_fallback is None:
                        platform_fallback = entry
                    if entry.get("persona_id") == persona_norm:
                        exact_match = entry
                        break

            chosen = exact_match or platform_fallback
            if chosen is None:
                valid_platforms = sorted(
                    {entry.get("platform", "") for entry in slices}
                )
                raise KeyError(
                    f"Platform '{platform}' is not supported in Historic Social Performance DB. "
                    f"Supported platforms: {valid_platforms}."
                )

            response = {
                "status": "success",
                "platform": chosen["platform"],
                "persona_id": persona_norm,
                "avg_engagement_rate_pct": float(
                    chosen["avg_engagement_rate_pct"]
                ),
                "avg_click_through_rate_pct": float(
                    chosen["avg_click_through_rate_pct"]
                ),
                "optimal_character_range": list(
                    chosen["optimal_character_range"]
                ),
                "top_performing_hook_patterns": list(
                    chosen["top_performing_hook_patterns"]
                ),
                "winning_structural_traits": list(
                    chosen["winning_structural_traits"]
                ),
                "top_historical_post_example": dict(
                    chosen["top_historical_post_example"]
                ),
                "llm_recovery_instructions": None,
            }
            return self.pii_redactor.redact_Data(response)


def get_social_performance_mcp_toolset_config() -> dict[str, Any]:
    """Return the ADK `McpToolset` stdio connection configuration for the Social Performance MCP server."""
    return {
        "server_name": "novapulse-social-performance-mcp-server",
        "command": sys.executable,
        "args": ["-m", "app.mcp_servers.social_performance_mcp_server"],
        "description": "MCP stdio server providing historical social media engagement benchmarks and top post exemplars.",
    }


def main() -> None:
    """Entrypoint for running the Historic Social Performance MCP server over stdio."""
    server = SocialPerformanceMcpServer()
    try:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("novapulse-social-performance-mcp-server")

        @mcp.tool(
            name="retrieve_historic_social_post_benchmarks",
            description="Retrieve historical social media engagement rates, CTR benchmarks, and winning post structures.",
        )
        def _mcp_query_benchmarks(
            platform: str,
            author_persona: str,
        ) -> dict[str, Any]:
            return server.query_benchmarks(
                platform=platform,
                author_persona=author_persona,
            )

        mcp.run(transport="stdio")
    except ImportError:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            params = request.get("params", {})
            response = server.query_benchmarks(
                platform=params.get("platform", "linkedin"),
                author_persona=params.get("author_persona", "founder_ceo"),
            )
            sys.stdout.write(json.dumps({"result": response}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
