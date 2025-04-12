"""
Mock modules for testing.
This file must be imported before any application modules.
"""

import sys
from unittest.mock import MagicMock

# Create message classes with proper string representation
class MockMessage:
    def __init__(self, content):
        self.content = content
    
    def __str__(self):
        return self.content
    
    def __repr__(self):
        return self.content

class MockUserMessage(MockMessage):
    pass

class MockAssistantMessage(MockMessage):
    pass

# Create the base module with our mock classes
class MockBase:
    Message = MockMessage
    UserMessage = MockUserMessage
    AssistantMessage = MockAssistantMessage

# Replace the MCP modules with our mocks
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = MagicMock()
sys.modules["mcp.server.fastmcp.prompts"] = MagicMock()
sys.modules["mcp.server.fastmcp.prompts.base"] = MockBase