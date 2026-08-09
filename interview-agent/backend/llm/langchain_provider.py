"""LangChain LLM provider."""

_mcp_executor = None

def set_mcp_executor(executor):
    """Register MCP executor."""
    global _mcp_executor
    _mcp_executor = executor

class LangChainProvider:
    """LangChain-based LLM provider."""
    def __init__(self):
        self.client = None
