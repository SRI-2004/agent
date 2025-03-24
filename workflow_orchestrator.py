import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

from tools.base import ToolResult
from tools import ToolRegistry

# Set up logging - only if not already configured elsewhere
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class WorkflowOrchestrator:
    """
    Orchestrates the workflow for audience segmentation and marketing in a chatbot style.
    Uses GPT-4 to handle conversations and coordinate tool execution.
    """
    
    def __init__(self):
        logger.info("Initializing WorkflowOrchestrator")
        # Initialize OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY not set in environment variables")
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        logger.info("Setting up OpenAI client")
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Load the tool registry with error handling
        try:
            logger.info("Initializing ToolRegistry")
            self.tool_registry = ToolRegistry()
            
            # Check if tools are available and log status
            initialization_status = self.tool_registry.get_initialization_status()
            for tool_name, status in initialization_status.items():
                if status == "initialized":
                    logger.info(f"Tool {tool_name} initialized successfully")
                else:
                    logger.warning(f"Tool {tool_name} failed to initialize: {status}")
            
            # Verify required tools are available
            required_tools = ["firecrawler", "serp_analysis", "category_tree"]
            for tool in required_tools:
                if not self.tool_registry.get_tool(tool):
                    logger.error(f"Required tool {tool} is not available")
                    raise ValueError(f"Required tool {tool} is not available")
                    
        except Exception as e:
            logger.error(f"Error initializing ToolRegistry: {str(e)}")
            raise ValueError(f"Failed to initialize tools: {str(e)}")
        
        # Workflow state
        logger.info("Setting up initial workflow state")
        self.conversation_history = []
        self.current_workflow_stage = "initial"
        self.product_data = {}
        self.market_data = {}
        self.category_data = {}
        self.final_results = {}
        
        # System prompts for different stages
        self.system_prompts = {
            "initial": """You are Audience Andy, an AI assistant specializing in audience segmentation and marketing strategy. 
            Keep your messages short and conversational.
            
            Your first step is simply to ask the user for a product URL to analyze.
            Don't provide detailed explanations unless the user asks for them.
            
            When responding to general questions, be helpful but concise.""",
            
            "url_analysis": """You are analyzing a product URL. Extract key information about the product 
            to prepare for audience segmentation. Provide detailed explanations about the product's characteristics 
            and how they relate to potential target audiences.
            
            When presenting your findings, go beyond basic details and share insights about:
            - The product's unique value proposition and how it differentiates from competitors
            - Specific features that appeal to different audience segments
            - Price positioning and what it signals about the target market
            - The tone and style of the product description and how it reflects brand identity
            
            Format your response with clear sections, bullet points, and thorough descriptions that help the user 
            understand the product from a marketing perspective.""",
            
            "market_research": """Based on the detailed product information, conduct comprehensive market research to identify 
            competitors and relevant keywords. Provide an in-depth analysis of the competitive landscape and search trends.
            
            In your response, include:
            - Detailed profiles of top competitors, including their positioning and target audiences
            - A thorough explanation of the keywords' relevance to the product and what they reveal about customer intent
            - Market trends and opportunities identified through the research
            - Insights about search volumes and competitive intensity
            
            Present your findings in a structured, educational format that helps the user understand the market context
            for their product. Explain how this market research will inform the next steps of audience segmentation.""",
            
            "category_mapping": """Map the product to appropriate marketing categories based on its features and target audience.
            Provide a comprehensive explanation of each category and why it's relevant to the product.
            
            For each identified category:
            - Explain why the product fits this category based on specific attributes and features
            - Describe typical audience characteristics associated with this category
            - Detail how the category relates to marketing channels and messaging approaches
            - Provide context about market size and growth within these categories
            
            Present your category mapping with clear hierarchy, showing relationships between categories and subcategories.
            Explain how these categories will be used to define precise audience segments in the next step.""",
            
            "audience_segmentation": """Create detailed, actionable audience segments based on the product analysis and category mapping.
            Develop rich audience profiles that would be interested in this product.
            
            For each audience segment:
            - Create a comprehensive demographic, psychographic, and behavioral profile
            - Explain their motivations, pain points, and how the product addresses their needs
            - Describe their typical buying journey and decision-making factors
            - Detail their media consumption habits and where to reach them
            - Explain why they are a high-value segment for this product specifically
            
            Support your audience segments with reasoning based on the product features, market research, and category mapping.
            Format your response with clear headings, bullet points, and thorough descriptions for each segment to provide 
            maximum actionable value.""",
            
            "marketing_strategy": """Develop comprehensive, data-driven marketing strategy recommendations based on the identified 
            audience segments. Create detailed, actionable plans for reaching and engaging each target audience.
            
            For each marketing strategy:
            - Provide a thorough explanation of the target audience segment and why this approach will resonate with them
            - Detail specific marketing channels with justification for their selection based on audience behavior
            - Create comprehensive messaging frameworks with key value propositions, tone, and language style
            - Suggest specific content types, formats, and creative approaches with examples
            - Include recommendations for timing, budget allocation, and performance metrics
            
            Present strategies in a structured format with clear rationale linking back to the product attributes and audience 
            insights. Provide actionable next steps that would help implement each strategy effectively.""",
            
            "final_summary": """Create a comprehensive, well-structured summary of the complete analysis including product details, 
            audience segments, and marketing recommendations. Present an actionable, strategic overview of all findings.
            
            Your summary should include:
            - A detailed product overview with key features and positioning insights
            - Comprehensive market analysis with competitive landscape and opportunity assessment
            - In-depth category classifications with clear explanations of relevance
            - Richly detailed audience segments with complete profiles and targeting criteria
            - Thorough marketing strategy recommendations with channel-specific approaches
            - Actionable next steps and implementation guidance
            
            Format your summary with clear headings, bullet points, and adequate detail in each section to serve as a 
            complete reference document.
            
            After providing the summary, you'll transition to a Q&A mode where the user can ask detailed follow-up questions 
            about any aspect of the analysis. Be prepared to provide additional depth on specific segments, strategies, or 
            implementation details based on all the data you've collected throughout the analysis process."""
        }
        logger.info("WorkflowOrchestrator initialization complete")
    
    async def start_conversation(self) -> str:
        """Start the conversation with an initial greeting"""
        logger.info("Starting new conversation")
        self.current_workflow_stage = "initial"
        self.conversation_history = []
        
        logger.info("Generating initial greeting message")
        initial_message = await self._get_ai_response("Hi there! I'm Audience Andy. Share a product URL with me, and I'll help you identify target audiences and marketing strategies for it.")
        logger.info("Conversation started")
        return initial_message
    
    async def process_message(self, user_message: str) -> str:
        """
        Process a user message and advance the workflow.
        
        Args:
            user_message: The message from the user
            
        Returns:
            The assistant's response
        """
        logger.info(f"Processing user message in stage: {self.current_workflow_stage}")
        
        # Log current data state for debugging
        logger.info(f"Current data state - Product data exists: {bool(self.product_data)}, "
                   f"Market data exists: {bool(self.market_data)}, "
                   f"Category data exists: {bool(self.category_data)}, "
                   f"Final results exists: {bool(self.final_results)}")
        
        # Log some basic data counts for debugging
        if self.product_data:
            feature_count = len(self.product_data.get('features', []))
            logger.info(f"Product data - Title: {self.product_data.get('title', 'None')}, Features count: {feature_count}")
        
        if self.market_data:
            keyword_count = len(self.market_data.get('keywords', []))
            competitor_count = len(self.market_data.get('competitors', []))
            logger.info(f"Market data - Keywords count: {keyword_count}, Competitors count: {competitor_count}")
            
        if self.category_data:
            category_count = len(self.category_data.get('matched_categories', []))
            segment_count = len(self.category_data.get('audience_segments', []))
            logger.info(f"Category data - Categories count: {category_count}, Segments count: {segment_count}")
        
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Check if the message contains a URL
        contains_url = any(word.startswith("http") for word in user_message.split())
        
        # Check for analysis request keywords
        analysis_keywords = ["analyze", "analysis", "research", "check", "explore", "look at", "review", "evaluate", "assess"]
        is_analysis_request = any(keyword in user_message.lower() for keyword in analysis_keywords)
        
        # Only start workflow if in initial stage and URL is provided
        if self.current_workflow_stage == "initial":
            # In initial stage, determine if we should start the workflow
            if contains_url and is_analysis_request:
                logger.info("Analysis requested with URL, starting workflow")
                return await self._handle_url_analysis(user_message)
            elif contains_url:
                logger.info("URL detected but no explicit analysis request, starting analysis anyway")
                return await self._handle_url_analysis(user_message)
            elif is_analysis_request:
                logger.info("Analysis requested but no URL provided")
                return await self._get_ai_response("I'd be happy to analyze a product for you. To get started, please share the product URL you'd like me to analyze.")
            else:
                # Just have a normal conversation
                logger.info("No analysis request or URL detected, maintaining conversation mode")
                return await self._get_ai_response(user_message)
        
        # Handle final summary stage
        elif self.current_workflow_stage == "final_summary":
            # Check if user is requesting to analyze a new product
            if contains_url and is_analysis_request:
                logger.info("New analysis requested in final_summary stage, restarting workflow")
                # Reset workflow state
                self.current_workflow_stage = "initial"
                self.product_data = {}
                self.market_data = {}
                self.category_data = {}
                self.final_results = {}
                # Start new analysis
                return await self._handle_url_analysis(user_message)
            else:
                # After final summary, stay in this stage to answer questions
                logger.info("In final_summary stage, processing follow-up question")
                # Don't modify the user message, just pass it through
                return await self._get_ai_response(user_message)
                
        # Handle any other message as a request to continue the analysis
        elif user_message.strip().lower() == "cancel" or user_message.strip().lower() == "stop":
            # Allow the user to cancel the workflow
            logger.info("User canceled the workflow, resetting to initial stage")
            self.current_workflow_stage = "initial"
            return await self._get_ai_response("I've canceled the analysis. If you'd like to analyze a product, please share a URL and ask me to analyze it.")
        else:
            # For any other message, continue the workflow based on current stage
            logger.info(f"User responded, continuing workflow from stage: {self.current_workflow_stage}")
            
            # Advance the workflow based on the current stage
            if self.current_workflow_stage == "url_analysis":
                logger.info("Advancing from url_analysis to market_research stage")
                self.current_workflow_stage = "market_research"
                return await self._handle_market_research()
            
            elif self.current_workflow_stage == "market_research":
                logger.info("Advancing from market_research to category_mapping stage")
                self.current_workflow_stage = "category_mapping"
                return await self._handle_category_mapping()
            
            elif self.current_workflow_stage == "category_mapping":
                logger.info("Advancing from category_mapping to audience_segmentation stage")
                self.current_workflow_stage = "audience_segmentation"
                return await self._handle_audience_segmentation()
            
            elif self.current_workflow_stage == "audience_segmentation":
                logger.info("Advancing from audience_segmentation to marketing_strategy stage")
                self.current_workflow_stage = "marketing_strategy"
                return await self._handle_marketing_strategy()
            
            elif self.current_workflow_stage == "marketing_strategy":
                logger.info("Advancing from marketing_strategy to final_summary stage")
                self.current_workflow_stage = "final_summary"
                return await self._handle_final_summary()
        
        # Default response if somehow we reach here
        logger.warning(f"Reached default response handler with stage: {self.current_workflow_stage}")
        return await self._get_ai_response("I'm not sure what to do next. If you'd like to analyze a product, please share a URL and ask me to analyze it. Or you can ask me a specific question about audience segmentation or marketing strategies.")
    
    async def _handle_url_analysis(self, user_message: str) -> str:
        """Extract URL and analyze the product"""
        logger.info("Handling URL analysis")
        # Simple URL extraction (can be improved with regex)
        url = None
        for word in user_message.split():
            if word.startswith("http"):
                url = word.strip()
                break
        
        if not url:
            logger.warning("No valid URL found in message")
            return await self._get_ai_response("I couldn't find a valid URL in your message. Please provide a product URL starting with http:// or https://.")
        
        # Execute firecrawler tool to analyze the product
        try:
            logger.info(f"Analyzing URL: {url}")
            
            logger.info("Executing firecrawler tool")
            result = await self.tool_registry.execute_tool("firecrawler", {"url": url, "depth": 2})
            
            if not result.success:
                logger.error(f"Error analyzing URL: {result.error}")
                return await self._get_ai_response(
                    f"I had trouble analyzing that product URL: {result.error}. "
                    f"Please try a different URL or try again later."
                )
            
            # Store product data
            logger.info("Successfully analyzed URL, storing product data")
            self.product_data = result.result
            
            # Validate product data has required fields
            if not self.product_data.get('title'):
                logger.warning("Product data missing title")
                self.product_data['title'] = url.split('/')[-1] or "Unknown Product"
            
            if not self.product_data.get('features') or len(self.product_data.get('features', [])) == 0:
                logger.warning("Product data missing features, adding placeholder feature")
                self.product_data['features'] = ["Product available online"]
            
            if not self.product_data.get('description'):
                logger.warning("Product data missing description")
                self.product_data['description'] = f"Online product at {url}"
            
            logger.debug(f"Product data: {json.dumps(self.product_data, indent=2)}")
            
            # Generate response with product information
            logger.info("Generating response with product information")
            product_info = f"""
            I've analyzed the product at {url}. Here's what I found:
            
            Product: {self.product_data.get('title', 'Unknown product')}
            Price: {self.product_data.get('price', 'Price not found')}
            
            Key features:
            {self._format_list(self.product_data.get('features', ['No features found']))}
            
            Description:
            {self.product_data.get('description', 'No description found')}
            
            I'll now continue with market research for this product...
            """
            
            # Get AI response for URL analysis
            url_analysis_response = await self._get_ai_response(product_info)
            
            # Advance workflow stage to market research
            logger.info("Advancing workflow stage to market_research")
            self.current_workflow_stage = "market_research"
            
            # Handle market research immediately
            market_research_response = await self._handle_market_research()
            
            # Return the combined response
            return f"{url_analysis_response}\n\n{market_research_response}"
            
        except Exception as e:
            logger.error(f"Error in URL analysis: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error while analyzing the product: {str(e)}. "
                f"Please try a different URL or try again later."
            )
    
    async def _handle_market_research(self) -> str:
        """Conduct market research for the product"""
        try:
            logger.info("Starting market research")
            
            # Verify we have valid product data
            if not self.product_data or not self.product_data.get('title'):
                logger.error("Product data missing or invalid for market research")
                return await self._get_ai_response(
                    "I'm missing the necessary product information to conduct market research. "
                    "Let's go back and analyze the product URL again."
                )
            
            # Get product title for search query
            product_title = self.product_data.get('title', '')
            logger.info(f"Using product title for market research: '{product_title}'")
            
            logger.info(f"Executing SERP analysis for query: '{product_title}'")
            result = await self.tool_registry.execute_tool("serp_analysis", {"query": product_title, "results_count": 10})
            
            if not result.success:
                logger.error(f"Error in market research: {result.error}")
                return await self._get_ai_response(
                    f"I had trouble conducting market research: {result.error}. "
                    f"Let's try again later or use a different approach."
                )
            
            # Store market data
            logger.info("Successfully completed market research, storing results")
            self.market_data = result.result
            
            # Validate market data has minimum required fields
            if not self.market_data.get('competitors') or len(self.market_data.get('competitors', [])) == 0:
                logger.warning("Market data missing competitors, adding placeholder")
                self.market_data['competitors'] = ["Similar products in the market"]
                
            if not self.market_data.get('keywords') or len(self.market_data.get('keywords', [])) == 0:
                logger.warning("Market data missing keywords, adding placeholder keywords")
                # Use product title words as keywords
                self.market_data['keywords'] = product_title.split()
                if len(self.market_data['keywords']) < 3:
                    self.market_data['keywords'].extend(["online", "quality", "popular"])
            
            logger.debug(f"Market data: {json.dumps(self.market_data, indent=2)}")
            
            # Generate response with market information
            logger.info("Generating response with market information")
            market_info = f"""
            I've researched the market for {product_title}. Here's what I found:
            
            Top competitors:
            {self._format_list(self.market_data.get('competitors', ['No competitors found']))}
            
            Related keywords:
            {self._format_list(self.market_data.get('keywords', ['No keywords found']))}
            
            Now I'll proceed with mapping this product to marketing categories...
            """
            
            # Get AI response for market research
            market_research_response = await self._get_ai_response(market_info)
            
            # Advance workflow stage to category_mapping
            logger.info("Advancing workflow stage to category_mapping")
            self.current_workflow_stage = "category_mapping"
            
            # Handle category mapping immediately
            category_mapping_response = await self._handle_category_mapping()
            
            # Return the combined response
            return f"{market_research_response}\n\n{category_mapping_response}"
            
        except Exception as e:
            logger.error(f"Error in market research: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error during market research: {str(e)}. "
                f"Let's try again later with more specific information."
            )
    
    async def _handle_category_mapping(self) -> str:
        """Map the product to marketing categories using optimized LLM approach"""
        try:
            logger.info("Starting optimized category mapping")
            
            # Verify we have valid product and market data
            if not self.product_data or not self.market_data:
                logger.error("Missing required data for category mapping")
                return await self._get_ai_response(
                    "I'm missing the necessary product or market information to perform category mapping. "
                    "Let's go back and make sure we have both product details and market research."
                )
            
            # Get product data for LLM context
            product_title = self.product_data.get('title', 'Unknown Product')
            product_description = self.product_data.get('description', '')
            product_features = self.product_data.get('features', [])
            product_keywords = self.market_data.get('keywords', [])
            
            # STEP 1: Get all categories in one call - both top-level and subcategories
            logger.info("Getting all marketing categories")
            
            # Get top-level categories first
            top_level_result = await self.tool_registry.execute_tool("category_tree", {
                "product_description": product_description,
                "mode": "explore_toplevel"
            })
            
            if not top_level_result.success:
                logger.error(f"Error getting categories: {top_level_result.error}")
                return await self._get_ai_response(
                    f"I had trouble exploring marketing categories: {top_level_result.error}. "
                    f"Let's try a different approach."
                )
                
            top_level_categories = top_level_result.result.get("categories", [])
            if not top_level_categories:
                logger.error("No categories found")
                return await self._get_ai_response(
                    "I couldn't find any marketing categories to explore. This is likely a technical issue. "
                    "Let's try a different approach to analyze your product."
                )
            
            # STEP 2: Prepare detailed category data including top categories and their subcategories
            # Use concurrent requests to get subcategories for all potential top categories
            subcategory_tasks = []
            for category in top_level_categories[:5]:  # Limit to top 5 categories for efficiency
                category_name = category["name"]
                task = self.tool_registry.execute_tool("category_tree", {
                    "product_description": product_description,
                    "mode": "explore_subcategories",
                    "parent_category": category_name
                })
                subcategory_tasks.append((category_name, task))
            
            # Build complete category hierarchy with all available subcategories
            category_hierarchy = []
            for category_name, task in subcategory_tasks:
                try:
                    result = await task
                    if result.success:
                        subcategories = result.result.get("subcategories", [])
                        # Find the original category object to get its description
                        category_obj = next((c for c in top_level_categories if c["name"] == category_name), {})
                        category_hierarchy.append({
                            "name": category_name,
                            "description": category_obj.get("description", ""),
                            "subcategories": subcategories
                        })
                    else:
                        logger.warning(f"Failed to get subcategories for {category_name}: {result.error}")
                        # Still include the category without subcategories
                        category_obj = next((c for c in top_level_categories if c["name"] == category_name), {})
                        category_hierarchy.append({
                            "name": category_name,
                            "description": category_obj.get("description", ""),
                            "subcategories": []
                        })
                except Exception as e:
                    logger.error(f"Error processing subcategories for {category_name}: {str(e)}")
            
            # STEP 3: Make a SINGLE LLM call to analyze everything at once
            # This replaces 3+ separate calls with just one comprehensive analysis
            analysis_prompt = f"""
            Analyze this product and perform three tasks:
            
            Product: {product_title}
            Description: {product_description}
            Features: {json.dumps(product_features)}
            Keywords: {json.dumps(product_keywords)}
            
            Available Marketing Categories (with subcategories):
            {json.dumps(category_hierarchy, indent=2)}
            
            TASK 1: Select the most relevant top-level categories (maximum 3)
            TASK 2: For each selected category, select the most relevant subcategories (maximum 5 per category)
            TASK 3: Create 3-4 detailed audience segments based on these categories
            
            Provide detailed explanations for all selections.
            
            Respond with a single JSON object containing all results:
            {{
                "selected_categories": [
                    {{
                        "category": "Category Name",
                        "explanation": "Detailed explanation of relevance",
                        "selected_subcategories": [
                            {{
                                "name": "Subcategory Name",
                                "explanation": "Explanation of why this subcategory is relevant"
                            }}
                        ]
                    }}
                ],
                "audience_segments": [
                    {{
                        "name": "Segment Name",
                        "description": "Detailed description of this audience segment",
                        "targeting_criteria": [
                            {{
                                "type": "interest/demographic/behavior",
                                "category": "Category name",
                                "subcategory": "Subcategory name (optional)",
                                "value": "Value (optional)"
                            }}
                        ]
                    }}
                ]
            }}
            """
            
            logger.info("Making single comprehensive LLM call for category analysis")
            try:
                analysis_response = await self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are an AI specializing in marketing categorization and audience segmentation. Provide comprehensive analysis with your response in JSON format."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                analysis_text = analysis_response.choices[0].message.content
                analysis_data = json.loads(analysis_text)
                
                # Extract the results
                selected_categories = analysis_data.get("selected_categories", [])
                audience_segments = analysis_data.get("audience_segments", [])
                
                if not selected_categories:
                    logger.warning("No categories selected by LLM, using default")
                    selected_categories = [{
                        "category": top_level_categories[0]["name"],
                        "explanation": "Most relevant category based on product description",
                        "selected_subcategories": []
                    }]
                
                if not audience_segments:
                    logger.warning("No audience segments created by LLM, using default")
                    audience_segments = [
                        {
                            "name": f"{product_title} Enthusiasts",
                            "description": f"People interested in {product_title} and similar products",
                            "targeting_criteria": [
                                {"type": "interest", "category": selected_categories[0]["category"]}
                            ]
                        },
                        {
                            "name": "Value Shoppers",
                            "description": "Price-conscious consumers looking for quality products",
                            "targeting_criteria": [
                                {"type": "behavior", "category": "Shopping Behavior", "value": "Price Comparison"}
                            ]
                        }
                    ]
                
            except Exception as e:
                logger.error(f"Error in LLM analysis: {str(e)}")
                # Fallback to simpler rule-based approach
                logger.warning("Using fallback rule-based category selection")
                selected_categories = [{
                    "category": top_level_categories[0]["name"],
                    "explanation": "Default selection based on product type",
                    "selected_subcategories": []
                }]
                
                # Get subcategories for the default category
                for item in category_hierarchy:
                    if item["name"] == selected_categories[0]["category"]:
                        subs = item.get("subcategories", [])
                        selected_categories[0]["selected_subcategories"] = [
                            {"name": sub["name"], "explanation": "Relevant to product features"} 
                            for sub in subs[:2]
                        ]
                
                # Create basic audience segments
                audience_segments = [
                    {
                        "name": f"{product_title} Enthusiasts",
                        "description": f"People interested in {product_title} and similar products",
                        "targeting_criteria": [
                            {"type": "interest", "category": selected_categories[0]["category"]}
                        ]
                    },
                    {
                        "name": "Value Shoppers",
                        "description": "Price-conscious consumers looking for quality products",
                        "targeting_criteria": [
                            {"type": "behavior", "category": "Shopping Behavior", "value": "Price Comparison"}
                        ]
                    }
                ]
            
            # Convert to the format expected by the rest of the system
            matched_categories = []
            final_categories = []
            
            for cat in selected_categories:
                category_name = cat["category"]
                explanation = cat.get("explanation", "")
                subcategories = cat.get("selected_subcategories", [])
                
                # Format for display
                final_categories.append({
                    "category": category_name,
                    "explanation": explanation,
                    "subcategories": subcategories
                })
                
                # Format for internal data structure
                matched_categories.append({
                    "category": category_name,
                    "subcategories": [{"name": sub["name"]} for sub in subcategories]
                })
            
            # Store the final results
            self.category_data = {
                "matched_categories": matched_categories,
                "audience_segments": audience_segments
            }
            
            # Generate response with category information
            logger.info("Generating response with category information")
            
            # Create a detailed response that includes the explanations
            category_info = "I've analyzed your product and identified these relevant marketing categories:\n\n"
            
            for cat in final_categories:
                category_info += f"## {cat['category']}\n"
                category_info += f"{cat['explanation']}\n\n"
                
                if cat['subcategories']:
                    category_info += "Relevant subcategories:\n"
                    for sub in cat['subcategories']:
                        category_info += f"- **{sub['name']}**: {sub['explanation']}\n"
                
                category_info += "\n"
            
            category_info += "\nNow I'll generate audience segments based on these categories..."
            
            # Get AI response for category mapping
            category_mapping_response = await self._get_ai_response(category_info)
            
            # Advance workflow stage to audience_segmentation
            logger.info("Advancing workflow stage to audience_segmentation")
            self.current_workflow_stage = "audience_segmentation"
            
            # Handle audience segmentation immediately
            audience_segmentation_response = await self._handle_audience_segmentation()
            
            # Return the combined response
            return f"{category_mapping_response}\n\n{audience_segmentation_response}"
            
        except Exception as e:
            logger.error(f"Error in category mapping: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error during category mapping: {str(e)}. "
                f"Let's try again with more detailed product information."
            )
    
    async def _handle_audience_segmentation(self) -> str:
        """Generate audience segments based on the analysis"""
        try:
            logger.info("Generating audience segments")
            
            # Verify we have valid category data
            if not self.category_data:
                logger.error("Missing category data for audience segmentation")
                return await self._get_ai_response(
                    "I'm missing the necessary category information to generate audience segments. "
                    "Let's go back and make sure we have proper category mapping."
                )
            
            # Get audience segments from the category tree tool
            audience_segments = self.category_data.get('audience_segments', [])
            
            # Log explicit information about segments
            if audience_segments:
                logger.info(f"Found {len(audience_segments)} audience segments in category data")
                for i, segment in enumerate(audience_segments):
                    logger.info(f"Segment {i+1}: {segment.get('name', 'Unnamed')}")
            else:
                logger.error("No audience segments found in category data")
                return await self._get_ai_response(
                    "I couldn't find audience segments in the category data. This is likely a technical issue. "
                    "Let me generate audience segments based on the product and category information we have."
                )
            
            # Store in final results
            self.final_results['audience_segments'] = audience_segments
            
            # Generate response with audience segments
            logger.info("Generating response with audience segments")
            segments_info = f"""
            Based on my analysis, here are the recommended audience segments for this product:
            
            {self._format_audience_segments(audience_segments)}
            
            Now I'll develop marketing strategies for these audience segments...
            """
            
            # Get AI response for audience segmentation
            audience_segmentation_response = await self._get_ai_response(segments_info)
            
            # Advance workflow stage to marketing_strategy
            logger.info("Advancing workflow stage to marketing_strategy")
            self.current_workflow_stage = "marketing_strategy"
            
            # Handle marketing strategy immediately
            marketing_strategy_response = await self._handle_marketing_strategy()
            
            # Return the combined response
            return f"{audience_segmentation_response}\n\n{marketing_strategy_response}"
            
        except Exception as e:
            logger.error(f"Error in audience segmentation: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error during audience segmentation: {str(e)}. "
                f"Let's try again with more detailed information about the product and its categories."
            )
    
    async def _handle_marketing_strategy(self) -> str:
        """Generate marketing strategy recommendations"""
        try:
            logger.info("Generating marketing strategies")
            
            # Combine all data for GPT-4 to generate marketing strategies
            combined_data = {
                "product": self.product_data,
                "market": self.market_data,
                "categories": self.category_data,
                "audience_segments": self.final_results.get('audience_segments', [])
            }
            
            logger.info("Creating marketing strategies prompt")
            # Use GPT-4 to generate marketing strategies
            strategies_prompt = f"""
            Based on the following product and audience data, generate 3-5 marketing strategy recommendations.
            For each strategy, include:
            1. The target audience segment
            2. Recommended marketing channels
            3. Key messaging points
            4. Suggested ad formats or content types
            
            Product: {json.dumps(self.product_data)}
            Market Research: {json.dumps(self.market_data)}
            Audience Segments: {json.dumps(self.final_results.get('audience_segments', []))}
            """
            
            # Add strategies to final results
            logger.info("Calling _generate_marketing_strategies method")
            marketing_strategies = await self._generate_marketing_strategies(strategies_prompt)
            logger.info(f"Generated {len(marketing_strategies)} marketing strategies")
            self.final_results['marketing_strategies'] = marketing_strategies
            
            logger.info("Creating response with marketing strategies")
            strategies_response = f"""
            Here are my recommended marketing strategies:
            
            {self._format_marketing_strategies(marketing_strategies)}
            
            Now I'll create a comprehensive summary of the entire analysis...
            """
            
            # Get AI response for marketing strategies
            marketing_strategy_response = await self._get_ai_response(strategies_response)
            
            # Advance workflow stage to final_summary
            logger.info("Advancing workflow stage to final_summary")
            self.current_workflow_stage = "final_summary"
            
            # Handle final summary immediately
            final_summary_response = await self._handle_final_summary()
            
            # Return the combined response
            return f"{marketing_strategy_response}\n\n{final_summary_response}"
            
        except Exception as e:
            logger.error(f"Error generating marketing strategies: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error while generating marketing strategies: {str(e)}. "
                f"Let's try again with more detailed information."
            )
    
    async def _handle_final_summary(self) -> str:
        """Generate a final summary of the analysis"""
        try:
            logger.info("Generating final summary")
            
            # Combine all data for the summary
            product_title = self.product_data.get('title', 'the analyzed product')
            logger.info(f"Creating final summary for product: {product_title}")
            
            summary = f"""
            # Complete Analysis for {product_title}
            
            ## Product Overview
            - **Name:** {self.product_data.get('title', 'N/A')}
            - **Price:** {self.product_data.get('price', 'N/A')}
            - **Key Features:** {', '.join(self.product_data.get('features', ['N/A'])[:3])}
            - **Description:** {self.product_data.get('description', 'N/A')}
            
            ## Market Analysis
            - **Top Competitors:** {', '.join(self.market_data.get('competitors', ['N/A'])[:5])}
            - **Related Keywords:** {', '.join(self.market_data.get('keywords', ['N/A'])[:8])}
            - **Search Volume:** {self.market_data.get('search_volume', 'N/A')}
            
            ## Category Mapping
            {self._summarize_categories(self.category_data.get('matched_categories', []))}
            
            ## Audience Segments
            {self._format_audience_segments(self.final_results.get('audience_segments', []))}
            
            ## Marketing Recommendations
            {self._format_marketing_strategies(self.final_results.get('marketing_strategies', []))}
            
            Thank you for using Audience Andy! You can now ask me questions about this analysis or any part of it that you'd like me to elaborate on. Or if you'd like to analyze another product, just share a new URL.
            """
            
            logger.info("Final summary generated successfully")
            return await self._get_ai_response(summary)
            
        except Exception as e:
            logger.error(f"Error generating final summary: {str(e)}", exc_info=True)
            return await self._get_ai_response(
                f"I encountered an error while generating the final summary: {str(e)}. "
                f"Please ask about specific parts of the analysis you're interested in."
            )
    
    async def _get_ai_response(self, message_content: str) -> str:
        """Get a response from OpenAI GPT-4"""
        try:
            logger.info("Getting AI response")
            # Add assistant message to history first
            self.conversation_history.append({"role": "assistant", "content": message_content})
            
            # Get the current system prompt based on workflow stage
            system_prompt = self.system_prompts.get(self.current_workflow_stage, self.system_prompts["initial"])
            
            # Add context to system prompt for follow-up questions in final_summary stage
            if self.current_workflow_stage == "final_summary" and self.product_data and self.final_results:
                system_prompt += "\n\nThe user is asking follow-up questions about the completed analysis. Use the accumulated data to provide detailed, specific answers about any aspect of the product, audience segments, or marketing strategies."
                
            logger.info(f"Using system prompt for stage: {self.current_workflow_stage}")
            
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            # Add last few messages from conversation history (limit to keep context manageable)
            messages.extend(self.conversation_history[-10:])
            
            logger.info("Calling OpenAI API for chat completion")
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use the appropriate GPT-4 model
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            
            ai_message = response.choices[0].message.content
            logger.info("Received AI response")
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            return f"I'm having trouble generating a response. Please try again. Error: {str(e)}"
    
    async def _generate_marketing_strategies(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate marketing strategies using GPT-4"""
        try:
            logger.info("Generating marketing strategies with GPT-4")
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a marketing strategy expert. Generate specific, actionable marketing strategies based on product and audience data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
            )
            
            strategy_text = response.choices[0].message.content
            logger.info("Received marketing strategies response from GPT-4")
            
            # Parse strategies (in a real implementation, you'd want more structured output)
            strategies = []
            strategy_blocks = strategy_text.split("\n\n")
            
            for i, block in enumerate(strategy_blocks):
                if block.strip():
                    strategies.append({
                        "id": i + 1,
                        "content": block.strip()
                    })
            
            logger.info(f"Parsed {len(strategies)} marketing strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating marketing strategies: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate marketing strategies: {str(e)}")
    
    # Helper methods for formatting output
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as bullet points"""
        logger.debug(f"Formatting list of {len(items) if items else 0} items")
        if not items:
            return "None found"
        return "\n".join([f"• {item}" for item in items])
    
    def _format_categories(self, categories: List[Dict[str, Any]]) -> str:
        """Format category information"""
        logger.debug(f"Formatting {len(categories) if categories else 0} categories")
        if not categories:
            return "No categories found"
        
        result = ""
        for category in categories:
            result += f"• {category.get('category', 'Unknown')}:\n"
            subcategories = category.get('subcategories', [])
            for subcategory in subcategories:
                result += f"  - {subcategory.get('name', 'Unknown')}\n"
        
        return result
    
    def _format_audience_segments(self, segments: List[Dict[str, Any]]) -> str:
        """Format audience segment information"""
        logger.debug(f"Formatting {len(segments) if segments else 0} audience segments")
        if not segments:
            return "No segments found"
        
        result = ""
        for segment in segments:
            result += f"• {segment.get('name', 'Unknown Segment')}:\n"
            result += f"  {segment.get('description', 'No description')}\n"
            
            # Add targeting criteria if available
            criteria = segment.get('targeting_criteria', [])
            if criteria:
                result += "  Targeting criteria:\n"
                for criterion in criteria[:3]:  # Limit to first 3 criteria
                    criterion_type = criterion.get('type', '')
                    category = criterion.get('category', '')
                    subcategory = criterion.get('subcategory', '')
                    value = criterion.get('value', '')
                    
                    criterion_text = f"{category}"
                    if subcategory:
                        criterion_text += f" > {subcategory}"
                    if value:
                        criterion_text += f" > {value}"
                    
                    result += f"    - {criterion_text}\n"
            
            result += "\n"
        
        return result
    
    def _format_marketing_strategies(self, strategies: List[Dict[str, Any]]) -> str:
        """Format marketing strategy information"""
        logger.debug(f"Formatting {len(strategies) if strategies else 0} marketing strategies")
        if not strategies:
            return "No strategies available"
        
        result = ""
        for strategy in strategies:
            result += f"### Strategy {strategy.get('id', '')}\n"
            result += f"{strategy.get('content', 'No details')}\n\n"
        
        return result
    
    def _summarize_categories(self, categories: List[Dict[str, Any]]) -> str:
        """Summarize category information for final summary"""
        logger.debug(f"Summarizing {len(categories) if categories else 0} categories")
        if not categories:
            return "- No specific categories identified"
        
        result = ""
        for i, category in enumerate(categories[:2]):  # Limit to top 2 categories
            result += f"- **{category.get('category', 'Unknown')}** "
            subcategories = category.get('subcategories', [])
            if subcategories:
                subcat_names = [s.get('name', '') for s in subcategories[:3]]
                result += f"({', '.join(subcat_names)})\n"
            else:
                result += "\n"
        
        return result


# Example of how to use the WorkflowOrchestrator
async def demo():
    logger.info("Starting WorkflowOrchestrator demo")
    orchestrator = WorkflowOrchestrator()
    
    # Start conversation
    response = await orchestrator.start_conversation()
    print(f"Assistant: {response}")
    
    # Mock user interaction
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            logger.info("Exiting demo")
            print("Exiting...")
            break
            
        response = await orchestrator.process_message(user_input)
        print(f"Assistant: {response}")


if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(demo()) 
    logger.info("Application finished") 