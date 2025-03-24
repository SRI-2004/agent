from typing import Dict, List, Type, Optional, Any
import logging
from importlib import import_module
import traceback
import os
from dotenv import load_dotenv

from tools.base import Tool, ToolResult
# Import tools individually to catch import errors
try:
    from tools.firecrawler_tool import FirecrawlerTool
    FIRECRAWLER_AVAILABLE = True
except ImportError as e:
    FIRECRAWLER_AVAILABLE = False
    logging.error(f"Error importing FirecrawlerTool: {str(e)}")

try:
    from tools.serp_analysis_tool import SerpAnalysisTool
    SERPAPI_AVAILABLE = True
except ImportError as e:
    SERPAPI_AVAILABLE = False
    logging.error(f"Error importing SerpAnalysisTool: {str(e)}")

try:
    from tools.category_tree_tool import CategoryTreeTool
    CATEGORY_TREE_AVAILABLE = True
except ImportError as e:
    CATEGORY_TREE_AVAILABLE = False
    logging.error(f"Error importing CategoryTreeTool: {str(e)}")

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for managing available tools"""
    
    _tools: Dict[str, Type[Tool]] = {}
    _instances: Dict[str, Tool] = {}
    _init_errors: Dict[str, str] = {}
    
    @classmethod
    def register(cls, tool_class: Type[Tool]) -> None:
        """Register a tool class in the registry."""
        try:
            # Create a temporary instance to get the name
            temp_instance = tool_class()
            tool_name = temp_instance._get_name()  # Use _get_name directly
            
            # Store the class regardless of availability - we'll check during instantiation
            cls._tools[tool_name] = tool_class
            
            # Check if the tool is available
            if not temp_instance.is_available():
                error_msg = f"Tool {tool_name} is not available: {getattr(temp_instance, 'initialization_error', 'Unknown error')}"
                logger.error(error_msg)
                cls._init_errors[tool_name] = error_msg
                # Don't return here - we still register the class
            else:
                logger.info(f"Successfully registered tool class: {tool_name}")
            
        except Exception as e:
            # If we can't get the name from the instance, use the class name
            tool_name = tool_class.__name__
            error_msg = f"Failed to register tool class {tool_name}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            cls._init_errors[tool_name] = error_msg
    
    @classmethod
    def get_tool_class(cls, name: str) -> Optional[Type[Tool]]:
        """Get a tool class by name."""
        tool_class = cls._tools.get(name)
        if not tool_class:
            logger.warning(f"Tool class not found: {name}")
        return tool_class
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[Tool]:
        """
        Get a tool instance by name.
        Creates a new instance if one doesn't exist.
        """
        if name not in cls._instances:
            tool_class = cls.get_tool_class(name)
            if tool_class:
                try:
                    logger.info(f"Creating instance of tool: {name}")
                    instance = tool_class()
                    
                    # Validate tool initialization
                    if not instance.is_available():
                        error_msg = f"Tool {name} is not available: {getattr(instance, 'initialization_error', 'Unknown error')}"
                        logger.error(error_msg)
                        cls._init_errors[name] = error_msg
                        cls._instances[name] = None
                    else:
                        cls._instances[name] = instance
                        logger.info(f"Successfully created instance of tool: {name}")
                except Exception as e:
                    error_msg = f"Error creating tool instance {name}: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    cls._init_errors[name] = error_msg
                    cls._instances[name] = None
            else:
                cls._init_errors[name] = f"Tool class {name} not found in registry"
                logger.error(f"Tool class {name} not found in registry")
        
        # Check if the instance is fully initialized
        instance = cls._instances.get(name)
        if instance is None:
            error_msg = cls._init_errors.get(name, f"Unknown initialization error for tool: {name}")
            logger.error(f"Tool instance {name} requested but not available. Error: {error_msg}")
            
        return instance
    
    @classmethod
    def get_all_tools(cls) -> List[Tool]:
        """Get instances of all available tools."""
        # Make sure all tools are instantiated
        for name in cls._tools.keys():
            if name not in cls._instances:
                cls.get_tool(name)  # This will handle initialization and error logging
        
        # Return only non-None instances
        return [instance for instance in cls._instances.values() if instance is not None]
    
    @classmethod
    def get_available_tool_names(cls) -> List[str]:
        """Get a list of all available tool names."""
        return list(cls._tools.keys())
    
    @classmethod
    def get_all_tools_as_dicts(cls) -> List[Dict[str, Any]]:
        """Get all tools as dictionaries"""
        tools = cls.get_all_tools()
        tool_dicts = []
        for tool in tools:
            try:
                tool_dicts.append(tool.to_dict())
            except Exception as e:
                logger.error(f"Error converting tool {tool.name} to dict: {str(e)}")
        return tool_dicts
    
    @classmethod
    def get_openai_functions(cls) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function format"""
        tools = cls.get_all_tools()
        functions = []
        for tool in tools:
            try:
                functions.append(tool.to_openai_function())
            except Exception as e:
                logger.error(f"Error converting tool {tool.name} to OpenAI function: {str(e)}")
        return functions
    
    @classmethod
    def get_initialization_status(cls) -> Dict[str, str]:
        """Get the initialization status of all tools"""
        # Ensure all tools have been initialized
        for name in cls._tools.keys():
            cls.get_tool(name)  # This will initialize the tool if not already initialized
            
        result = {}
        for name in cls._tools.keys():
            if name in cls._instances and cls._instances[name] is not None:
                result[name] = "initialized"
            else:
                result[name] = cls._init_errors.get(name, "unknown error")
        return result
    
    @classmethod
    async def execute_tool(cls, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with parameters"""
        logger.info(f"Executing tool requested: {tool_name}")
        tool = cls.get_tool(tool_name)
        
        if not tool:
            error_msg = f"Tool not found or not available: {tool_name}"
            logger.error(error_msg)
            if tool_name in cls._init_errors:
                error_msg += f". Initialization error: {cls._init_errors[tool_name]}"
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_name
            )
        
        try:
            logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
            result = await tool.execute(parameters)
            logger.info(f"Tool execution completed: {tool_name}, success: {result.success}")
            return result
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_name
            )

# Load environment variables
load_dotenv()

# Direct registration of tool instances - more reliable than class registration
logger.info("Directly registering tool instances...")

# Clean initialization to avoid redundant instantiations
firecrawler_tool = None
serp_analysis_tool = None
category_tree_tool = None

try:
    if FIRECRAWLER_AVAILABLE:
        logger.info("Creating FirecrawlerTool instance")
        firecrawler_tool = FirecrawlerTool()
        firecrawler_name = firecrawler_tool._get_name()
        if firecrawler_tool.is_available():
            logger.info(f"Successfully created FirecrawlerTool with name: {firecrawler_name}")
            ToolRegistry._tools[firecrawler_name] = FirecrawlerTool
            ToolRegistry._instances[firecrawler_name] = firecrawler_tool
        else:
            logger.error(f"FirecrawlerTool not available: {firecrawler_tool.initialization_error}")
            ToolRegistry._init_errors[firecrawler_name] = firecrawler_tool.initialization_error
    else:
        logger.error("FirecrawlerTool not available - skipping registration")
except Exception as e:
    logger.error(f"Error registering FirecrawlerTool: {str(e)}")

try:
    if SERPAPI_AVAILABLE:
        logger.info("Creating SerpAnalysisTool instance")
        serp_analysis_tool = SerpAnalysisTool()
        serp_name = serp_analysis_tool._get_name()
        if serp_analysis_tool.is_available():
            logger.info(f"Successfully created SerpAnalysisTool with name: {serp_name}")
            ToolRegistry._tools[serp_name] = SerpAnalysisTool
            ToolRegistry._instances[serp_name] = serp_analysis_tool
        else:
            logger.error(f"SerpAnalysisTool not available: {serp_analysis_tool.initialization_error}")
            ToolRegistry._init_errors[serp_name] = serp_analysis_tool.initialization_error
    else:
        logger.error("SerpAnalysisTool not available - skipping registration")
except Exception as e:
    logger.error(f"Error registering SerpAnalysisTool: {str(e)}")

try:
    if CATEGORY_TREE_AVAILABLE:
        logger.info("Creating CategoryTreeTool instance")
        category_tree_tool = CategoryTreeTool()
        category_name = category_tree_tool._get_name()
        if category_tree_tool.is_available():
            logger.info(f"Successfully created CategoryTreeTool with name: {category_name}")
            ToolRegistry._tools[category_name] = CategoryTreeTool
            ToolRegistry._instances[category_name] = category_tree_tool
        else:
            logger.error(f"CategoryTreeTool not available: {category_tree_tool.initialization_error}")
            ToolRegistry._init_errors[category_name] = category_tree_tool.initialization_error
    else:
        logger.error("CategoryTreeTool not available - skipping registration")
except Exception as e:
    logger.error(f"Error registering CategoryTreeTool: {str(e)}")

# Create a global instance of the tool registry
tool_registry = ToolRegistry()

# Log the current state of registered tools at startup
logger.info(f"Registered tools: {tool_registry.get_available_tool_names()}")
logger.info(f"Tool initialization status: {tool_registry.get_initialization_status()}") 