import os
import logging
import traceback
from typing import Dict, Any, List, Optional
import json
import re
from dotenv import load_dotenv
# Import for direct search API usage
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
    logging.info("SerpAPI library imported successfully")
except ImportError as e:
    SERPAPI_AVAILABLE = False
    logging.error(f"Error importing SerpAPI library: {str(e)}")

from tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

class SerpAnalysisTool(Tool):
    """Tool for analyzing search engine results for market research"""
    
    def __init__(self):
        """Initialize the SerpAnalysisTool with API key"""
        super().__init__()
        # Explicitly load .env file
        load_dotenv()
        
        self.api_key = os.getenv("SERPAPI_KEY")
        
        if not SERPAPI_AVAILABLE:
            self.initialization_error = "SerpAPI library not installed or not found"
            logger.error("Failed to initialize SerpAnalysisTool: SerpAPI library not available")
            return
            
        if not self.api_key:
            self.initialization_error = "SERPAPI_KEY not set in environment variables"
            logger.error("Failed to initialize SerpAnalysisTool: SERPAPI_KEY not set")
            return
            
        logger.info("SerpAnalysisTool initialized successfully")
    
    def _get_name(self) -> str:
        return "serp_analysis"
    
    def _get_description(self) -> str:
        return "Conducts market research using search engine results. This tool analyzes search results for a product query to identify competitors, related products, and popular keywords. Use this to understand the competitive landscape for a product."
    
    def _get_parameters(self) -> Dict[str, Any]:
        return {
            "query": {"type": "string", "description": "The search query for the product or category to analyze"},
            "results_count": {"type": "integer", "description": "Number of search results to analyze (5-20)", "default": 10}
        }
    
    def _get_required_parameters(self) -> List[str]:
        return ["query"]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute serp_analysis tool to research competitors"""
        try:
            # Check if the tool is available
            if not self.is_available():
                error_msg = f"SerpAPI tool is not available: {self.initialization_error or 'Unknown error'}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg,
                    tool_name=self.name
                )
                
            query = parameters.get("query", "")
            results_count = min(max(parameters.get("results_count", 10), 5), 20)  # Limit between 5-20
            
            if not query:
                return ToolResult(
                    success=False,
                    error="Please provide a valid search query.",
                    tool_name=self.name
                )
            
            logger.info(f"Using SerpAPI to analyze query: {query}")
            # Perform the search
            search = GoogleSearch({
                "q": query,
                "num": results_count,
                "api_key": self.api_key,
                "location": "United States"
            })
            results = search.get_dict()
            
            # Parse the results
            organic_results = results.get("organic_results", [])
            
            if not organic_results:
                error_msg = f"No organic results found for query: {query}"
                logger.warning(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg,
                    tool_name=self.name
                )
                
            # Create the result data
            market_data = self._extract_market_data_from_serpapi(organic_results, query)
            
            logger.info(f"Successfully analyzed market data for query: {query}")
            logger.info(f"Found {len(market_data.get('competitors', []))} competitors and {len(market_data.get('keywords', []))} keywords")
            
            return ToolResult(
                success=True,
                result=market_data,
                error=None,
                tool_name=self.name
            )
                
        except Exception as e:
            error_msg = f"Error executing serp_analysis: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
    
    def _extract_market_data_from_serpapi(self, organic_results: List[Dict], query: str) -> Dict[str, Any]:
        """Extract market data from SerpAPI results"""
        # Analyze the results to extract market data
        competitors = []
        related_keywords = []
        domain_frequencies = {}
        
        # Extract company names and domains from results
        for result in organic_results:
            title = result.get("title", "")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            
            # Extract domain
            domain_match = re.search(r"https?://(?:www\.)?([^/]+)", link)
            if domain_match:
                domain = domain_match.group(1)
                # Count domain frequency
                domain_frequencies[domain] = domain_frequencies.get(domain, 0) + 1
                
                # Extract company name from domain or title
                company_name = domain.split('.')[0]
                if company_name not in ['amazon', 'ebay', 'walmart', 'bestbuy', 'target']:
                    # This looks like a specific company, not just a marketplace
                    if company_name not in [c.lower() for c in competitors]:
                        competitors.append(company_name.title())
            
            # Extract keywords from title and snippet
            all_text = f"{title} {snippet}"
            words = re.findall(r'\b\w+\b', all_text.lower())
            
            # Filter out common words and find product-related terms
            stopwords = ['the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'of', 'for', 'in', 'to', 'with']
            for word in words:
                if (len(word) > 3 and word not in stopwords and 
                    word not in query.lower() and 
                    word not in related_keywords and
                    not word.isdigit()):
                    related_keywords.append(word)
        
        # Sort competitors by frequency in results
        sorted_competitors = sorted(
            competitors, 
            key=lambda x: domain_frequencies.get(x.lower(), 0),
            reverse=True
        )
        
        # Create market research data
        market_data = {
            "competitors": sorted_competitors[:5],  # Top 5 competitors
            "keywords": related_keywords[:10],      # Top 10 related keywords
            "search_volume": "medium",              # Placeholder since we don't have real data
            "query": query
        }
        
        return market_data 