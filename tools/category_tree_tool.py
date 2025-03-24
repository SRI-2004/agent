import json
import os
import logging
import traceback
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dotenv import load_dotenv

from tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)

class CategoryTreeTool(Tool):
    """Tool for navigating and analyzing marketing categories."""
    
    def __init__(self):
        """Initialize the CategoryTreeTool."""
        super().__init__()
        # Explicitly load .env file
        load_dotenv()
        
        # Load the category tree from the JSON file
        try:
            self.categories = self._load_categories()
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Error initializing CategoryTreeTool: {str(e)}")
    
    def _get_name(self) -> str:
        return "category_tree"
    
    def _get_description(self) -> str:
        return "Navigates a tree of marketing categories to find the best match for a product"
    
    def _get_parameters(self) -> Dict[str, Any]:
        return {
            "product_description": {"type": "string", "description": "Description of the product"},
            "product_features": {"type": "array", "items": {"type": "string"}, "description": "List of product features"},
            "product_keywords": {"type": "array", "items": {"type": "string"}, "description": "List of keywords from product"},
            "max_categories": {"type": "integer", "description": "Maximum number of top-level categories to return", "default": 3},
            "max_subcategories": {"type": "integer", "description": "Maximum number of subcategories per category", "default": 5},
            "mode": {"type": "string", "description": "Mode of operation: 'match' for automatic matching, 'explore_toplevel' for getting all top-level categories, 'explore_subcategories' for getting subcategories of a specific category", "default": "match"},
            "parent_category": {"type": "string", "description": "Parent category to get subcategories for (used in explore_subcategories mode)"}
        }
    
    def _get_required_parameters(self) -> List[str]:
        return ["product_description"]
    
    def _load_categories(self) -> Dict:
        """Load the marketing categories from the JSON file."""
        # Try multiple potential locations
        potential_paths = [
            # Look in current directory
            Path("marketing_categories.json"),
            # Look in the same directory as this file
            Path(os.path.dirname(os.path.abspath(__file__))) / "marketing_categories.json",
            # Look in data directory relative to this file
            Path(os.path.dirname(os.path.abspath(__file__))) / ".." / "data" / "marketing_categories.json",
            # Look in data directory at root
            Path("data") / "marketing_categories.json",
        ]
        
        for path in potential_paths:
            try:
                logger.info(f"Attempting to load marketing categories from: {path}")
                with open(path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Successfully loaded marketing categories from: {path}")
                return data
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load from {path}: {e}")
                continue
        
        # If we get here, all paths failed
        error_msg = "Failed to load marketing categories from any path. Marketing categories file not found."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Navigate the category tree to find the best categories for a product.
        
        Args:
            parameters: Dict containing:
                - product_description: Description of the product
                - product_features: List of product features
                - product_keywords: List of keywords from product
                - max_categories: Maximum number of top-level categories to return (default: 3)
                - max_subcategories: Maximum number of subcategories per category (default: 5)
                - mode: Mode of operation (match, explore_toplevel, explore_subcategories)
                - parent_category: Parent category to get subcategories for
        
        Returns:
            ToolResult with matched categories and audience segments
        """
        try:
            # Check if tool is available
            if not self.is_available():
                error_msg = f"Category tree tool is not available: {self.initialization_error}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    error=error_msg,
                    tool_name=self.name
                )
            
            product_description = parameters.get("product_description", "")
            product_features = parameters.get("product_features", [])
            product_keywords = parameters.get("product_keywords", [])
            max_categories = parameters.get("max_categories", 3)
            max_subcategories = parameters.get("max_subcategories", 5)
            mode = parameters.get("mode", "match")
            parent_category = parameters.get("parent_category", "")
            
            # Different modes of operation
            if mode == "explore_toplevel":
                logger.info("Getting all top-level categories for LLM to choose from")
                top_categories = self._get_all_top_level_categories()
                
                result = {
                    "categories": top_categories,
                    "mode": "explore_toplevel",
                    "audience_segments": []  # No segments in exploration mode
                }
                
                logger.info(f"Returning {len(top_categories)} top-level categories for LLM exploration")
                return ToolResult(
                    success=True,
                    result=result,
                    error=None,
                    tool_name=self.name
                )
                
            elif mode == "explore_subcategories" and parent_category:
                logger.info(f"Getting subcategories for category: {parent_category}")
                subcategories = self._get_subcategories_for_category(parent_category)
                
                result = {
                    "parent_category": parent_category,
                    "subcategories": subcategories,
                    "mode": "explore_subcategories",
                    "audience_segments": []  # No segments in exploration mode
                }
                
                logger.info(f"Returning {len(subcategories)} subcategories for parent category: {parent_category}")
                return ToolResult(
                    success=True,
                    result=result,
                    error=None,
                    tool_name=self.name
                )
            
            # Default "match" mode - existing behavior
            # Check if this is a request for top-level categories (empty input)
            if not product_description.strip() and not product_features and not product_keywords:
                logger.info("Detected request for top-level categories (empty input data)")
            else:
                logger.info(f"Executing category tree tool with description: {product_description[:50]}...")
            
            # For now, implement a simple keyword matching algorithm
            # In a real implementation, this would use embeddings or more sophisticated matching
            matched_categories = self._match_categories(
                product_description, 
                product_features,
                product_keywords,
                max_categories,
                max_subcategories
            )
            
            audience_segments = self._generate_audience_segments(matched_categories)
            
            result = {
                "matched_categories": matched_categories,
                "audience_segments": audience_segments,
                "mode": "match"
            }
            
            logger.info(f"Category mapping completed with {len(matched_categories)} categories and {len(audience_segments)} audience segments")
            
            return ToolResult(
                success=True,
                result=result,
                error=None,
                tool_name=self.name
            )
            
        except Exception as e:
            error_msg = f"Error executing category tree tool: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=self.name
            )
    
    def _match_categories(
        self, 
        description: str, 
        features: List[str],
        keywords: List[str],
        max_categories: int,
        max_subcategories: int
    ) -> List[Dict[str, Any]]:
        """
        Match product info to categories.
        
        This is a simplified implementation. In a production system, this would use:
        - Semantic similarity with embeddings
        - Classification models
        - Keyword extraction and matching
        
        For now, we'll implement a basic keyword matching approach.
        """
        logger.info(f"Starting category matching with description length: {len(description)}, "
                   f"features count: {len(features)}, keywords count: {len(keywords)}")
        
        # Check if we have any meaningful input data
        if not description.strip() and not features and not keywords:
            logger.info("No input data provided - returning all top-level categories instead of matching")
            # Return all top-level categories when no input is provided
            all_categories = []
            for category in self.categories.get("categories", []):
                all_categories.append({
                    "category": category["name"],
                    "description": category.get("description", ""),
                    "score": 5,  # Default score
                    "subcategories": []  # Empty subcategories since no matching was done
                })
            
            # Sort alphabetically and return up to max_categories
            all_categories.sort(key=lambda x: x["category"])
            logger.info(f"Returning {min(len(all_categories), max_categories)} top-level categories without matching")
            return all_categories[:max_categories]
            
        # For all other cases, continue with the existing matching logic
        # Combine all product info into a single string for matching
        all_text = " ".join([description] + features + keywords).lower()
        logger.info(f"Combined text length for matching: {len(all_text)}")
        
        # Store matches with a simple score based on keyword occurrences
        category_scores = []
        
        # Log available categories for debugging
        available_categories = [cat.get("name", "Unnamed") for cat in self.categories.get("categories", [])]
        logger.info(f"Available top-level categories for matching: {available_categories}")
        
        for category in self.categories.get("categories", []):
            score = 0
            cat_name = category["name"].lower()
            
            # Match category name
            if cat_name in all_text:
                score += 10
                logger.debug(f"Found exact match for category: {cat_name}")
            
            # Match partial category name (more lenient)
            for word in cat_name.split():
                if len(word) > 3 and word in all_text:  # Only consider words longer than 3 chars
                    score += 3
                    logger.debug(f"Found partial match for category word: {word}")
            
            # Match category description
            if "description" in category and category["description"].lower() in all_text:
                score += 5
                logger.debug(f"Found match in category description for: {cat_name}")
                
            # Also check for related keywords in the entire text
            related_keywords = self._get_keywords_for_category(category["name"])
            matched_keywords = []
            for keyword in related_keywords:
                if keyword.lower() in all_text:
                    score += 2
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                logger.debug(f"Matched keywords for {cat_name}: {matched_keywords}")
            
            # Even if no direct match, give a small base score to ensure we have some categories
            if score == 0:
                # Give a small score based on general relevance
                if "general" in cat_name or "product" in cat_name or "consumer" in cat_name:
                    score += 1
                    logger.debug(f"Assigning base score to general category: {cat_name}")
            
            if score > 0:
                subcategories = self._match_subcategories(category, all_text, max_subcategories)
                category_scores.append({
                    "category": category["name"],
                    "description": category.get("description", ""),
                    "score": score,
                    "subcategories": subcategories
                })
        
        # Sort by score and take the top categories
        category_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # If no categories matched, provide at least one default category
        if not category_scores:
            logger.warning("No category matches found, creating default category")
            # Look for a generic category in the available categories
            default_category = next((cat for cat in self.categories.get("categories", []) 
                                    if "general" in cat["name"].lower() or "consumer" in cat["name"].lower()),
                                    None)
            
            if default_category:
                logger.info(f"Using existing general category: {default_category['name']}")
                category_scores.append({
                    "category": default_category["name"],
                    "description": default_category.get("description", "General products category"),
                    "score": 1,
                    "subcategories": self._match_subcategories(default_category, all_text, max_subcategories)
                })
            else:
                logger.info("Creating completely new default category")
                # Create a completely new default category
                category_scores.append({
                    "category": "General Consumer Products",
                    "description": "Products intended for general consumer use",
                    "score": 1,
                    "subcategories": [{
                        "name": "Online Products",
                        "description": "Products available for purchase online",
                        "score": 1
                    }]
                })
        
        result = category_scores[:max_categories]
        logger.info(f"Returning {len(result)} categories. Top category: {result[0]['category'] if result else 'None'}")
        return result
    
    def _match_subcategories(
        self, 
        category: Dict[str, Any],
        all_text: str,
        max_subcategories: int
    ) -> List[Dict[str, Any]]:
        """Match subcategories based on text."""
        subcategory_scores = []
        
        if "subcategories" not in category:
            return []
            
        for subcategory in category["subcategories"]:
            score = 0
            # Match subcategory name
            if subcategory["name"].lower() in all_text:
                score += 5
            
            # Match subcategory description if available
            if "description" in subcategory and subcategory["description"].lower() in all_text:
                score += 3
                
            # Match values if available
            if "values" in subcategory:
                for value in subcategory["values"]:
                    if value.lower() in all_text:
                        score += 2
            
            # Recursively match nested subcategories if any
            nested_subcategories = []
            if "subcategories" in subcategory:
                nested_subcategories = self._match_subcategories(subcategory, all_text, max_subcategories)
                
            if score > 0 or nested_subcategories:
                subcategory_data = {
                    "name": subcategory["name"],
                    "description": subcategory.get("description", ""),
                    "score": score
                }
                
                if nested_subcategories:
                    subcategory_data["subcategories"] = nested_subcategories
                    
                if "values" in subcategory:
                    # Find matched values
                    matched_values = [v for v in subcategory["values"] if v.lower() in all_text]
                    if matched_values:
                        subcategory_data["matched_values"] = matched_values
                
                subcategory_scores.append(subcategory_data)
        
        # Sort by score and take the top subcategories
        subcategory_scores.sort(key=lambda x: x["score"], reverse=True)
        return subcategory_scores[:max_subcategories]
    
    def _get_keywords_for_category(self, category_name: str) -> List[str]:
        """
        Get related keywords for a category.
        
        In a real implementation, this would be more sophisticated,
        possibly using a precomputed mapping or embedding similarity.
        """
        # Basic keyword mapping
        keyword_map = {
            "Demographics": ["age", "gender", "education", "marital status", "ethnicity"],
            "Financial": ["money", "income", "wealth", "finance", "investment", "budget"],
            "Home": ["house", "apartment", "residence", "property", "rent", "mortgage"],
            "Life Events": ["wedding", "marriage", "engagement", "birthday", "anniversary", "graduation"],
            "Interests": ["hobby", "passion", "activity", "entertainment", "leisure"],
            "Shopping and Fashion": ["clothes", "style", "trend", "retail", "purchase", "buy"],
            "Technology": ["tech", "gadget", "device", "digital", "electronic", "computer"],
            "Behaviors": ["habit", "pattern", "routine", "lifestyle", "behavior"]
        }
        
        return keyword_map.get(category_name, [])
    
    def _generate_audience_segments(self, matched_categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate audience segments based on matched categories.
        
        In a real implementation, this would be more sophisticated,
        using predefined audience segment templates and rules.
        """
        logger.info(f"Generating audience segments from {len(matched_categories)} matched categories")
        audience_segments = []
        
        # Generate audience segments based on top categories and their subcategories
        for category_match in matched_categories:
            category_name = category_match["category"]
            subcategories = category_match.get("subcategories", [])
            
            logger.info(f"Creating segments for category: {category_name} with {len(subcategories)} subcategories")
            
            # Create a primary segment for this category
            primary_segment = {
                "name": f"{category_name} Enthusiasts",
                "description": f"People interested in {category_name.lower()} products and services",
                "targeting_criteria": [
                    {
                        "type": "interest",
                        "category": category_name
                    }
                ]
            }
            
            # Add subcategory criteria
            for subcategory in subcategories:
                subcategory_name = subcategory["name"]
                
                # Add criteria based on subcategory
                primary_segment["targeting_criteria"].append({
                    "type": "interest",
                    "category": category_name,
                    "subcategory": subcategory_name
                })
                
                # Add criteria based on matched values if available
                if "matched_values" in subcategory:
                    for value in subcategory["matched_values"]:
                        primary_segment["targeting_criteria"].append({
                            "type": "interest",
                            "category": category_name,
                            "subcategory": subcategory_name,
                            "value": value
                        })
                
                # Create a specialized segment for notable subcategories
                if subcategory.get("score", 0) > 3:
                    segment = {
                        "name": f"{subcategory_name} Seekers",
                        "description": f"Consumers specifically looking for {subcategory_name.lower()} in the {category_name.lower()} category",
                        "targeting_criteria": [
                            {
                                "type": "interest",
                                "category": category_name,
                                "subcategory": subcategory_name
                            },
                            {
                                "type": "behavior",
                                "category": "Shopping Behavior",
                                "value": "Product Research"
                            }
                        ]
                    }
                    audience_segments.append(segment)
            
            audience_segments.append(primary_segment)
            
            # Create additional audience segments based on the category
            if "Technology" in category_name or "Electronics" in category_name:
                audience_segments.append({
                    "name": "Tech Early Adopters",
                    "description": "People who seek out the latest technology products and innovations",
                    "targeting_criteria": [
                        {
                            "type": "interest",
                            "category": category_name
                        },
                        {
                            "type": "behavior",
                            "category": "Technology",
                            "value": "Early Adopter" 
                        }
                    ]
                })
            
            if "Fashion" in category_name or "Clothing" in category_name or "Apparel" in category_name:
                audience_segments.append({
                    "name": "Fashion-Forward Consumers",
                    "description": "Style-conscious consumers who follow trends and fashion innovations",
                    "targeting_criteria": [
                        {
                            "type": "interest",
                            "category": category_name
                        },
                        {
                            "type": "demographic",
                            "category": "Shopping Behavior",
                            "value": "Trend-Driven"
                        }
                    ]
                })
            
            if "Home" in category_name or "Furniture" in category_name or "Decor" in category_name:
                audience_segments.append({
                    "name": "Home Improvement Enthusiasts",
                    "description": "People actively enhancing or renovating their living spaces",
                    "targeting_criteria": [
                        {
                            "type": "interest",
                            "category": category_name
                        },
                        {
                            "type": "life_event",
                            "category": "Home",
                            "value": "Moving/Renovating"
                        }
                    ]
                })
        
        # Always add these general segments if we have few specific segments
        if len(audience_segments) < 3:
            logger.info("Adding general audience segments due to limited specific segments")
            
            # Add a value-conscious segment
            audience_segments.append({
                "name": "Value-Conscious Shoppers",
                "description": "Price-sensitive consumers who compare options before purchasing",
                "targeting_criteria": [
                    {
                        "type": "behavior",
                        "category": "Shopping Behavior",
                        "value": "Price Comparison"
                    },
                    {
                        "type": "behavior",
                        "category": "Shopping Behavior",
                        "value": "Coupon User"
                    }
                ]
            })
            
            # Add a convenience shopper segment
            audience_segments.append({
                "name": "Convenience Shoppers",
                "description": "Consumers who prioritize ease of purchase and quick delivery",
                "targeting_criteria": [
                    {
                        "type": "behavior",
                        "category": "Shopping Behavior",
                        "value": "Online Shopper"
                    },
                    {
                        "type": "behavior",
                        "category": "Shopping Behavior",
                        "value": "Fast Shipping"
                    }
                ]
            })
            
            # Add a quality-focused segment
            audience_segments.append({
                "name": "Quality-Focused Consumers",
                "description": "Shoppers who prioritize product quality and durability over price",
                "targeting_criteria": [
                    {
                        "type": "behavior",
                        "category": "Shopping Behavior",
                        "value": "Quality-Driven"
                    },
                    {
                        "type": "demographic",
                        "category": "Income",
                        "value": "Above Average"
                    }
                ]
            })
        
        logger.info(f"Generated {len(audience_segments)} audience segments")
        return audience_segments
    
    def _get_all_top_level_categories(self) -> List[Dict[str, Any]]:
        """Get all top-level categories with descriptions for LLM to choose from."""
        logger.info("Getting all top-level categories")
        top_categories = []
        
        for category in self.categories.get("categories", []):
            top_categories.append({
                "name": category["name"],
                "description": category.get("description", ""),
                "has_subcategories": "subcategories" in category and len(category["subcategories"]) > 0
            })
        
        # Sort alphabetically for consistent presentation
        top_categories.sort(key=lambda x: x["name"])
        logger.info(f"Found {len(top_categories)} top-level categories")
        return top_categories
    
    def _get_subcategories_for_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Get subcategories for a specific parent category."""
        logger.info(f"Looking for subcategories of: {category_name}")
        subcategories = []
        
        # Find the specified category
        for category in self.categories.get("categories", []):
            if category["name"] == category_name:
                # Found the category, extract its subcategories
                for subcategory in category.get("subcategories", []):
                    subcategories.append({
                        "name": subcategory["name"],
                        "description": subcategory.get("description", ""),
                        "has_subcategories": "subcategories" in subcategory and len(subcategory["subcategories"]) > 0,
                        "values": subcategory.get("values", [])
                    })
                break
        
        # Sort alphabetically for consistent presentation
        subcategories.sort(key=lambda x: x["name"])
        logger.info(f"Found {len(subcategories)} subcategories for {category_name}")
        return subcategories 