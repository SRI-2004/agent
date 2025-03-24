import os
import logging
from typing import Dict, Any, List, Optional
import json
import re
import traceback
from dotenv import load_dotenv
# Add firecrawl import for direct API usage
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
    logging.info("Firecrawl library imported successfully")
except ImportError as e:
    FIRECRAWL_AVAILABLE = False
    logging.error(f"Error importing Firecrawl library: {str(e)}")

from tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

class FirecrawlerTool(Tool):
    """Tool for analyzing product websites using Firecrawler"""
    
    def __init__(self):
        """Initialize the FirecrawlerTool with API key"""
        super().__init__()
        # Explicitly load .env file
        load_dotenv()
        
        self.firecrawl_app = None
        
        # Check if the Firecrawl library is available
        if not FIRECRAWL_AVAILABLE:
            self.initialization_error = "Firecrawl library not installed"
            logger.error("Failed to initialize FirecrawlerTool: Firecrawl library not installed")
            return
            
        # Get API key from environment
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            self.initialization_error = "FIRECRAWL_API_KEY not set in environment variables"
            logger.error("Failed to initialize FirecrawlerTool: FIRECRAWL_API_KEY not set")
            return
            
        # Try to initialize the FirecrawlApp
        try:
            self.firecrawl_app = FirecrawlApp(api_key=self.api_key)
            logger.info("FirecrawlApp initialized successfully")
        except Exception as e:
            self.initialization_error = f"Error initializing FirecrawlApp: {str(e)}"
            logger.error(f"Failed to initialize FirecrawlerTool: {self.initialization_error}")
    
    def _get_name(self) -> str:
        return "firecrawler"
    
    def _get_description(self) -> str:
        return "Analyzes a product webpage to extract detailed information. Use this to obtain comprehensive product details including features, pricing, specifications, and positioning directly from a URL. Provides structured data that can be used for further analysis."
    
    def _get_parameters(self) -> Dict[str, Any]:
        return {
            "url": {"type": "string", "description": "The product webpage URL to analyze (must be a valid http/https URL)"},
            "depth": {"type": "integer", "description": "Crawling depth (1 for basic info, 2 for more details, 3 for comprehensive analysis)", "default": 1}
        }
    
    def _get_required_parameters(self) -> List[str]:
        return ["url"]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute firecrawler tool to analyze a website"""
        # Check if the tool is available
        if not self.is_available():
            error_msg = f"Firecrawler tool is not available: {self.initialization_error or 'Unknown error'}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
            
        url = parameters.get("url", "")
        depth = parameters.get("depth", 1)
        
        logger.info(f"Executing firecrawler tool with URL: {url}, depth: {depth}")
        
        # Validate URL
        if not (url.startswith("http://") or url.startswith("https://")):
            error_msg = "Invalid URL format. Please provide a URL starting with http:// or https://."
            logger.error(f"URL validation failed: {error_msg}")
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
        
        # Check for common example/fictional domains
        example_domains = ["example.com", "exampleheadphones.com", "domain.com", 
                        "example.org", "placeholder", "sample", "test.com"]
        
        if any(domain in url.lower() for domain in example_domains):
            error_msg = "The URL appears to be a fictional or example domain. Please provide a real product URL."
            logger.error(f"URL validation failed: {error_msg}")
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
        
        try:
            # Verify that FirecrawlApp is available
            if not self.firecrawl_app:
                error_msg = f"Firecrawl is not available: {self.initialization_error or 'Unknown error'}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg,
                    tool_name=self.name
                )
                
            # Use Firecrawl API directly
            logger.info(f"Calling FirecrawlApp.scrape_url with URL: {url}")
            scrape_result = self.firecrawl_app.scrape_url(
                url, 
                params={'formats': ['markdown', 'html']}
            )
            
            if not scrape_result:
                error_msg = "Empty result returned from Firecrawl API"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg,
                    tool_name=self.name
                )
                
            logger.info(f"Successfully received response from Firecrawl API for URL: {url}")
            
            # Parse the result to extract product information
            product_data = self._parse_firecrawl_result(scrape_result)
            
            logger.info(f"Successfully parsed product data from URL: {url}")
            logger.info(f"Product title: {product_data.get('title', 'N/A')}")
            logger.info(f"Product price: {product_data.get('price', 'N/A')}")
            
            return ToolResult(
                success=True,
                result=product_data,
                error=None,
                tool_name=self.name
            )
                
        except Exception as e:
            error_msg = f"Error executing firecrawler: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
    
    def _parse_firecrawl_result(self, scrape_result: Dict) -> Dict[str, Any]:
        """Parse the Firecrawl API response to extract product information"""
        product_data = {
            "title": "",
            "price": "",
            "description": "",
            "features": [],
            "specifications": {},
            "images": []
        }
        
        try:
            # Extract content from Firecrawl result
            if "title" in scrape_result:
                product_data["title"] = scrape_result["title"]
            
            if "content" in scrape_result:
                content = scrape_result["content"]
                
                # Look for price patterns
                price_patterns = [
                    r'\$\d+(?:\.\d{2})?',  # $XX.XX
                    r'Price:?\s*\$?\d+(?:\.\d{2})?',  # Price: $XX.XX
                    r'Cost:?\s*\$?\d+(?:\.\d{2})?'  # Cost: $XX.XX
                ]
                
                for pattern in price_patterns:
                    prices = re.findall(pattern, content)
                    if prices:
                        product_data["price"] = prices[0]
                        break
                
                # Extract features (assuming bullet points or numbered lists)
                feature_patterns = [
                    r'[-•*]\s*(.*?)(?=[-•*]|\n|$)',  # Bullet points
                    r'\d+\.\s*(.*?)(?=\d+\.|\n|$)'   # Numbered points
                ]
                
                features = []
                for pattern in feature_patterns:
                    found_features = re.findall(pattern, content)
                    features.extend([f.strip() for f in found_features if f.strip()])
                
                product_data["features"] = features[:10]  # Limit to 10 features
                
                # Basic description extraction (first few paragraphs)
                paragraphs = re.split(r'\n\s*\n', content)
                if paragraphs:
                    product_data["description"] = paragraphs[0].strip()
            
            # Extract images if available
            if "images" in scrape_result:
                product_data["images"] = scrape_result["images"][:5]  # Limit to 5 images
                
        except Exception as e:
            logger.error(f"Error parsing Firecrawl result: {str(e)}")
        
        return product_data
    
   