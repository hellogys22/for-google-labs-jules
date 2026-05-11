import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

from core.db import get_db

def seed_database():
    print("Loading environment variables...")
    load_dotenv()

    db = get_db()
    if db is None:
        print("Failed to connect to MongoDB. Please ensure MONGODB_URI is correctly set in your environment.")
        return

    print(f"Connected to database: {db.name}. Seeding data...")

    # Clear existing collections for a clean seed
    for col in ['products', 'reels', 'earnings', 'daily_reports', 'agent_logs']:
        db[col].drop()

    now = datetime.utcnow()
    product_id_1 = str(uuid.uuid4())
    product_id_2 = str(uuid.uuid4())

    # 1. Seed Products
    print("Seeding 'products'...")
    db.products.insert_many([
        {
            'id': product_id_1,
            'name': 'Viral Electric Chopper',
            'price': 299,
            'platform': 'meesho',
            'rating': 4.5,
            'affiliate_url': 'https://meesho.com/affiliate/demo1',
            'image_url': 'https://example.com/chopper.jpg',
            'video_path': 'videos/raw/demo1.mp4',
            'embedding': [0.1] * 1536, # Dummy embedding
            'performance_score': 0.8,
            'created_at': now - timedelta(days=2)
        },
        {
            'id': product_id_2,
            'name': 'Magic Cleaning Sponge',
            'price': 150,
            'platform': 'deodap',
            'rating': 4.2,
            'affiliate_url': 'https://deodap.com/affiliate/demo2',
            'image_url': 'https://example.com/sponge.jpg',
            'video_path': None,
            'embedding': [0.2] * 1536,
            'performance_score': 0.5,
            'created_at': now - timedelta(days=1)
        }
    ])

    # 2. Seed Reels
    print("Seeding 'reels'...")
    db.reels.insert_many([
        {
            'product_id': product_id_1,
            'script_json': {
                'hook': 'Wait! Look at this!',
                'body': 'Best chopper ever.',
                'cta': 'Link in bio.',
                'caption': 'Check this out!',
                'hashtags': '#viral'
            },
            'video_path': 'videos/final/demo1.mp4',
            'audio_path': 'audio/demo1.mp3',
            'status': 'posted',
            'instagram_post_id': 'ig_demo_123',
            'posted_at': now - timedelta(hours=12),
            'created_at': now - timedelta(days=1)
        },
        {
            'product_id': product_id_2,
            'script_json': {
                'hook': 'Cleaning hack!',
                'body': 'Sponge magic.',
                'cta': 'Link in bio.',
                'caption': 'So clean.',
                'hashtags': '#cleaning'
            },
            'video_path': 'videos/final/demo2.mp4',
            'audio_path': 'audio/demo2.mp3',
            'status': 'ready',
            'instagram_post_id': None,
            'posted_at': None,
            'created_at': now
        }
    ])

    # 3. Seed Earnings
    print("Seeding 'earnings'...")
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    db.earnings.insert_many([
        {
            'date': yesterday_str,
            'platform': 'meesho',
            'clicks': 250,
            'conversions': 5,
            'commission_inr': 150.0,
            'created_at': now - timedelta(days=1)
        },
        {
            'date': today_str,
            'platform': 'meesho',
            'clicks': 500,
            'conversions': 15,
            'commission_inr': 450.0,
            'created_at': now
        }
    ])

    # 4. Seed Daily Reports
    print("Seeding 'daily_reports'...")
    db.daily_reports.insert_one({
        'date': today_str,
        'total_clicks': 500,
        'total_conversions': 15,
        'total_commission_inr': 450.0,
        'best_product': product_id_1,
        'worst_product': product_id_2,
        'created_at': now
    })

    # 5. Seed Agent Logs
    print("Seeding 'agent_logs'...")
    db.agent_logs.insert_many([
        {
            "agent_name": "research_agent",
            "status": "success",
            "message": "Found 10 products.",
            "created_at": now - timedelta(hours=5)
        },
        {
            "agent_name": "content_agent",
            "status": "success",
            "message": "Generated 1 reel.",
            "created_at": now - timedelta(hours=4)
        },
        {
            "agent_name": "post_agent",
            "status": "success",
            "message": "Posted reel successfully. ID: ig_demo_123",
            "created_at": now - timedelta(hours=3)
        }
    ])

    print("Demo data seeded successfully! You can now view it in your MongoDB database.")

if __name__ == "__main__":
    seed_database()