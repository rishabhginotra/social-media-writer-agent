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

"""Model Context Protocol (MCP) Demo Servers for the Social Media Writer Agent.

Provides standalone MCP server implementations (stdio / FastMCP compatible) and
in-process adapters for:
1. CRM Audience & Account Intelligence Server (`crm_mcp_server.py`)
2. Marketing Campaign & Messaging Database Server (`marketing_db_mcp_server.py`)
3. Historic Social Media Performance Benchmark Server (`social_performance_mcp_server.py`)
"""

from app.mcp_servers.crm_mcp_server import CrmMcpServer, get_crm_mcp_toolset_config
from app.mcp_servers.marketing_db_mcp_server import (
    MarketingDatabaseMcpServer,
    get_marketing_mcp_toolset_config,
)
from app.mcp_servers.social_performance_mcp_server import (
    SocialPerformanceMcpServer,
    get_social_performance_mcp_toolset_config,
)

__all__ = [
    "CrmMcpServer",
    "MarketingDatabaseMcpServer",
    "SocialPerformanceMcpServer",
    "get_crm_mcp_toolset_config",
    "get_marketing_mcp_toolset_config",
    "get_social_performance_mcp_toolset_config",
]
