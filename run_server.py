import uvicorn
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

if __name__ == "__main__":
    # Set logging to INFO for both our app and uvicorn
    logging.getLogger("workflow_orchestrator").setLevel(logging.INFO)
    logging.getLogger("api").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    print("Starting Audience Andy server with enhanced logging...")
    
    # Run the server with proper logging
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        log_level="info",
        access_log=True
    ) 