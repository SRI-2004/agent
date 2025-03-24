# Audience Andy

A comprehensive product analysis system designed to help users analyze products and identify potential target audiences for marketing. The system uses AI-powered tools to analyze product URLs, conduct market research, and generate audience segments and marketing strategies.

## Features

- **Product URL Analysis**: Extract product information from any URL
- **Market Research**: Identify competitors and related keywords
- **Audience Segmentation**: Generate targeted audience segments based on product details
- **Marketing Strategy Recommendations**: Get personalized marketing strategies for your product
- **Chat Interface**: Interact with the system through a conversational interface
- **GPT-4 Powered**: Utilizes OpenAI's GPT-4 for natural language processing
- **Interactive Dashboard**: Visualize audience segments and marketing data

## System Architecture

The project consists of:

1. **Tool System**: A collection of specialized tools for different analysis tasks
   - **FirecrawlerTool**: Web scraping for product analysis
   - **SerpAnalysisTool**: Search engine results analysis for market research
   - **CategoryTreeTool**: Mapping products to marketing categories

2. **Workflow Orchestrator**: Coordinates the tools in a sequential workflow and manages the conversation

3. **FastAPI Backend**: RESTful API service that handles tool execution and workflow management

4. **Streamlit Frontend**: Interactive web application with a chat interface and visualization dashboard

## Setup

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- OpenAI API key
- SerpAPI key (for market research)
- Firecrawl API key (for web scraping)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd audience-andy
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SERPAPI_KEY=your_serpapi_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   API_URL=http://localhost:8000  # For development
   ```

### Running the Application

There are multiple ways to run the application:

#### Option 1: All-in-one launcher (Recommended)
```
python run.py
```
This will start both the FastAPI backend and Streamlit frontend in a single command.

#### Option 2: Run services separately

1. Start the FastAPI backend:
   ```
   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

2. In a separate terminal, start the Streamlit frontend:
   ```
   streamlit run streamlit_app.py
   ```

### Accessing the Application

Once running:

- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Frontend**: http://localhost:8501

## Usage

1. Open the Streamlit interface in your browser (http://localhost:8501)
2. Share a product URL with Audience Andy in the chat
3. Review the extracted product information 
4. Follow the chatbot through the analysis steps
5. Explore the Dashboard tab to see visualizations of the analysis
6. Get recommended audience segments and marketing strategies
7. Use the "New Analysis" button to start over with a different product

## API Endpoints

The FastAPI backend provides the following endpoints:

- `POST /api/start`: Start a new conversation
- `POST /api/message`: Send a message and get a response
- `GET /api/status`: Get the current status of the workflow
- `POST /api/reset`: Reset the workflow to the initial state

## Directory Structure

```
audience-andy/
├── api.py                  # FastAPI backend
├── streamlit_app.py        # Streamlit frontend
├── workflow_orchestrator.py # Chatbot workflow manager
├── run.py                  # All-in-one launcher
├── tools/                  # Analysis tools
│   ├── __init__.py         # Tool registry
│   ├── base.py             # Base tool class
│   ├── category_tree_tool.py # Category mapping tool
│   ├── firecrawler_tool.py # Web scraping tool
│   └── serp_analysis_tool.py # Market research tool
├── data/                   # Data files
│   └── marketing_categories.json # Marketing category data
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for GPT-4
- `SERPAPI_KEY`: Your SerpAPI key for search engine analysis
- `FIRECRAWL_API_KEY`: Your Firecrawl API key for web scraping
- `API_URL`: URL of the FastAPI backend (default: http://localhost:8000)
- `PORT`: (Optional) Port for the FastAPI backend (default: 8000)

## Development

To extend or modify this project:

- Add new tools in the `tools/` directory
- Update the workflow orchestrator for new workflow stages
- Modify the Streamlit frontend for new visualizations
- Add new API endpoints in the FastAPI backend

## Troubleshooting

- If you can't connect to the API, ensure the backend is running and check your `API_URL` environment variable
- If visualizations don't appear, make sure you have the required data at the current workflow stage
- For API errors, check the FastAPI documentation at http://localhost:8000/docs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4
- SerpAPI for search engine data
- Firecrawl for web scraping capabilities
- Streamlit and FastAPI for the amazing framework 