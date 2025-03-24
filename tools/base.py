from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class ToolResult:
    """Standardized result from tool execution"""
    def __init__(self, 
                success: bool, 
                result: Optional[Dict[str, Any]] = None, 
                error: Optional[str] = None,
                tool_name: Optional[str] = None):
        self.success = success
        self.result = result
        self.error = error
        self.tool_name = tool_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "status": "success" if self.success else "error",
            "tool_name": self.tool_name,
            "result": self.result,
            "error": self.error
        }

class Tool(ABC):
    """Base class for all tools"""
    
    def __init__(self):
        """Initialize the tool with error handling"""
        self.initialization_error = None
        self._name = None
        self._description = None
        self._parameters = None
        self._required_parameters = None
    
    @property
    def name(self) -> str:
        """The name of the tool"""
        if self._name is None:
            try:
                self._name = self._get_name()
            except Exception as e:
                self.initialization_error = f"Failed to get tool name: {str(e)}"
                logger.error(self.initialization_error)
                return "unknown_tool"
        return self._name
    
    @property
    def description(self) -> str:
        """Description of what the tool does"""
        if self._description is None:
            try:
                self._description = self._get_description()
            except Exception as e:
                self.initialization_error = f"Failed to get tool description: {str(e)}"
                logger.error(self.initialization_error)
                return "Tool description not available"
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Parameter definitions for the tool"""
        if self._parameters is None:
            try:
                self._parameters = self._get_parameters()
            except Exception as e:
                self.initialization_error = f"Failed to get tool parameters: {str(e)}"
                logger.error(self.initialization_error)
                return {}
        return self._parameters
    
    @property
    def required_parameters(self) -> List[str]:
        """List of required parameter names"""
        if self._required_parameters is None:
            try:
                self._required_parameters = self._get_required_parameters()
            except Exception as e:
                self.initialization_error = f"Failed to get required parameters: {str(e)}"
                logger.error(self.initialization_error)
                return []
        return self._required_parameters
    
    def is_available(self) -> bool:
        """Check if the tool is properly initialized and available for use"""
        return self.initialization_error is None
    
    @abstractmethod
    def _get_name(self) -> str:
        """Get the name of the tool"""
        pass
    
    @abstractmethod
    def _get_description(self) -> str:
        """Get the description of the tool"""
        pass
    
    @abstractmethod
    def _get_parameters(self) -> Dict[str, Any]:
        """Get the parameter definitions"""
        pass
    
    @abstractmethod
    def _get_required_parameters(self) -> List[str]:
        """Get the list of required parameters"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool definition to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "required_parameters": self.required_parameters,
            "initialization_error": self.initialization_error
        }
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required_parameters
                }
            }
        } 