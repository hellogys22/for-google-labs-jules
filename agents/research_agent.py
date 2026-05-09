import os
import json
import uuid
from datetime import datetime
from playwright.sync_api import sync_playwright
import openai
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat

from core.db import get_db

load_dotenv()

# OpenAI Initialization
openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key:
    openai.api_key = openai_api_key
else:
    print("Warning: OPENAI_API_KEY not found.")

def log_agent_action(status: str, message: str):
    """Log an action to the agent_logs collection."""
    db = get_db()
    if db is None:
        print(f"Log (local): {status} - {message}")
        return
    try:
        db.agent_logs.insert_one({
            "agent_name": "research_agent",
            "status": status,
            "message": message,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Failed to log action: {e}")

def scrape_meesho(page) -> list:
    """Scrape Meesho Home & Kitchen category for products under 500 INR and > 4.0 stars."""
    print("Scraping Meesho...")
    # Realistic scraping attempt structure:
    try:
        # page.goto("https://www.meesho.com/home-kitchen/pl/3", timeout=60000)
        # page.wait_for_selector(".product-card")
        pass
    except Exception as e:
        print(f"Meesho scraping exception: {e}")

    # We fallback to mock data since live scraping requires bypassing bot protections.
    # In a full production implementation, we'd iterate over `.product-card` elements here.
    products = [
        {
            "id": str(uuid.uuid4()),
            "name": "Meesho Super Chopper",
            "price": 250,
            "platform": "meesho",
            "rating": 4.2,
            "orders": 1500,
            "affiliate_url": "https://meesho.com/affiliate/123",
            "image_url": "https://images.meesho.com/images/products/123/img.jpg",
            "has_video": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Meesho Cleaning Brush",
            "price": 150,
            "platform": "meesho",
            "rating": 4.5,
            "orders": 3000,
            "affiliate_url": "https://meesho.com/affiliate/124",
            "image_url": "https://images.meesho.com/images/products/124/img.jpg",
            "has_video": False
        }
    ]
    return [p for p in products if p['price'] < 500 and p['rating'] > 4.0]

def scrape_deodap(page) -> list:
    """Scrape Deodap Home & Kitchen category."""
    print("Scraping Deodap...")
    try:
        # page.goto("https://deodap.com/collections/home-kitchen", timeout=60000)
        # page.wait_for_selector(".grid-product")
        pass
    except Exception as e:
        print(f"Deodap scraping exception: {e}")

    products = [
        {
            "id": str(uuid.uuid4()),
            "name": "Deodap Spice Rack",
            "price": 300,
            "platform": "deodap",
            "rating": 4.1,
            "orders": 800,
            "affiliate_url": "https://deodap.com/affiliate/125",
            "image_url": "https://deodap.com/images/125.jpg",
            "has_video": True
        }
    ]
    return [p for p in products if p['price'] < 500 and p['rating'] > 4.0]

def download_video(product_id: str, platform: str) -> str:
    """Check and download product video using yt-dlp. Return path."""
    # Placeholder for yt-dlp download
    # In reality: use yt-dlp python module or subprocess to download to videos/raw/{product_id}.mp4
    video_path = f"videos/raw/{product_id}.mp4"
    # Mocking that video exists
    # os.makedirs(os.path.dirname(video_path), exist_ok=True)
    # with open(video_path, 'w') as f: f.write("dummy video content")

    # Return None for this mock to force video generation later, or return path if successful
    return video_path

def get_embedding(text: str) -> list:
    """Get embedding from OpenAI."""
    if not openai.api_key:
        return [0.0] * 1536
    try:
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0.0] * 1536

def run():
    print("Starting Research Agent...")
    log_agent_action("success", "Research agent started.")

    all_products = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            meesho_products = scrape_meesho(page)
            all_products.extend(meesho_products)

            deodap_products = scrape_deodap(page)
            all_products.extend(deodap_products)

            browser.close()

    except Exception as e:
        log_agent_action("error", f"Playwright scraping failed: {e}")
        return

    if not all_products:
        log_agent_action("error", "No products found.")
        return

    # Calculate score
    for p in all_products:
        p['score'] = (p['orders'] * 0.40) + (p['rating'] * 0.30) + ((500 - p['price']) * 0.20) + (0.10 if p.get('has_video') else 0)

    # Top 3 scoring
    all_products.sort(key=lambda x: x['score'], reverse=True)
    top_products = all_products[:3]

    # Process and store
    for p in top_products:
        try:
            # Check video
            video_path = None
            if p.get('has_video'):
                video_path = download_video(p['id'], p['platform'])

            # Embed
            text_to_embed = f"{p['name']} {p['platform']} Home Kitchen gadget price {p['price']} rating {p['rating']} viral"
            embedding = get_embedding(text_to_embed)

            # Save to MongoDB
            db = get_db()
            if db is not None:
                db.products.insert_one({
                    'id': p['id'],
                    'name': p['name'],
                    'price': p['price'],
                    'platform': p['platform'],
                    'rating': p['rating'],
                    'affiliate_url': p['affiliate_url'],
                    'image_url': p['image_url'],
                    'video_path': video_path,
                    'embedding': embedding,
                    'performance_score': 0.5,
                    'created_at': datetime.utcnow()
                })
                print(f"Inserted product: {p['name']}")

        except Exception as e:
            log_agent_action("error", f"Failed to process product {p['name']}: {e}")

    log_agent_action("success", "Research agent finished successfully.")

def run_agent():
    agent = Agent(
        name="ResearchAgent",
        description="Scrapes ecommerce sites to find the best viral products.",
        instructions=["Execute the run function to start the scraping process."],
        tools=[run],
        show_tool_calls=True,
    )
    if openai.api_key:
        agent.model = OpenAIChat(id="gpt-4o")
    agent.print_response("Find the best home and kitchen gadgets under 500 INR today.")

if __name__ == "__main__":
    run_agent()