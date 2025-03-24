import os
import sys
import traceback
import logging
from dotenv import load_dotenv
from tools import ToolRegistry
from tools.firecrawler_tool import FirecrawlerTool
from tools.serp_analysis_tool import SerpAnalysisTool
from tools.category_tree_tool import CategoryTreeTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("Checking environment variables...")
    load_dotenv()
    
    required_keys = ["OPENAI_API_KEY", "SERPAPI_KEY", "FIRECRAWL_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            missing_keys.append(key)
            logger.error(f"Missing required environment variable: {key}")
        else:
            logger.info(f"Found environment variable: {key} = {value[:4]}...")
    
    if missing_keys:
        print("❌ Missing required environment variables:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nPlease add these variables to your .env file.")
        return False
    
    print("✅ All required environment variables are set.")
    return True

def check_tools_directly():
    """Check each tool class directly without going through the registry"""
    print("Directly checking individual tool classes...")
    
    all_ok = True
    
    # Check FirecrawlerTool
    print("\nFirecrawlerTool:")
    try:
        tool = FirecrawlerTool()
        if tool.is_available():
            print(f"✅ FirecrawlerTool initialized successfully")
            logger.info("FirecrawlerTool initialized successfully")
        else:
            print(f"❌ FirecrawlerTool failed: {tool.initialization_error}")
            logger.error(f"FirecrawlerTool failed: {tool.initialization_error}")
            all_ok = False
    except Exception as e:
        print(f"❌ FirecrawlerTool instantiation error: {str(e)}")
        logger.error(f"FirecrawlerTool instantiation error: {str(e)}")
        logger.error(traceback.format_exc())
        all_ok = False
    
    # Check SerpAnalysisTool
    print("\nSerpAnalysisTool:")
    try:
        tool = SerpAnalysisTool()
        if tool.is_available():
            print(f"✅ SerpAnalysisTool initialized successfully")
            logger.info("SerpAnalysisTool initialized successfully")
        else:
            print(f"❌ SerpAnalysisTool failed: {tool.initialization_error}")
            logger.error(f"SerpAnalysisTool failed: {tool.initialization_error}")
            all_ok = False
    except Exception as e:
        print(f"❌ SerpAnalysisTool instantiation error: {str(e)}")
        logger.error(f"SerpAnalysisTool instantiation error: {str(e)}")
        logger.error(traceback.format_exc())
        all_ok = False
    
    # Check CategoryTreeTool
    print("\nCategoryTreeTool:")
    try:
        tool = CategoryTreeTool()
        if tool.is_available():
            print(f"✅ CategoryTreeTool initialized successfully")
            logger.info("CategoryTreeTool initialized successfully")
        else:
            print(f"❌ CategoryTreeTool failed: {tool.initialization_error}")
            logger.error(f"CategoryTreeTool failed: {tool.initialization_error}")
            all_ok = False
    except Exception as e:
        print(f"❌ CategoryTreeTool instantiation error: {str(e)}")
        logger.error(f"CategoryTreeTool instantiation error: {str(e)}")
        logger.error(traceback.format_exc())
        all_ok = False
    
    return all_ok

def check_tools_registry():
    """Check if all tools are properly initialized using the registry"""
    print("\nChecking tool initialization through registry...")
    
    try:
        # Create registry and get status
        tool_registry = ToolRegistry()
        status = tool_registry.get_initialization_status()
        
        all_ok = True
        for tool_name, status_msg in status.items():
            if status_msg == "initialized":
                print(f"✅ {tool_name}: Initialized successfully")
                logger.info(f"Tool {tool_name} initialized successfully")
            else:
                print(f"❌ {tool_name}: {status_msg}")
                logger.error(f"Tool {tool_name} failed to initialize: {status_msg}")
                all_ok = False
        
        if not all_ok:
            print("\nDetailed error messages:")
            for tool_name, status_msg in status.items():
                if status_msg != "initialized":
                    print(f"\n{tool_name}:")
                    print(f"  Error: {status_msg}")
        
        return all_ok
    except Exception as e:
        error_msg = f"Error accessing ToolRegistry: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all checks"""
    print("="*50)
    print("Audience Andy - System Check")
    print("="*50)
    
    # First check environment variables
    env_ok = check_environment_variables()
    print("\n")
    
    # Then check tools directly
    tools_direct_ok = check_tools_directly()
    print("\n")
    
    # Then check through registry
    tools_registry_ok = check_tools_registry()
    
    print("\n")
    if env_ok and (tools_direct_ok or tools_registry_ok):
        print("✅ System check complete - environment ready to run.")
        return 0
    else:
        print("❌ Some checks failed. Please resolve the issues before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 