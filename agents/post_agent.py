import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from agno.agent import Agent

from core.db import get_db

load_dotenv()

access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")

def log_agent_action(status: str, message: str):
    db = get_db()
    if db is None:
        print(f"Log (local): {status} - {message}")
        return
    try:
        db.agent_logs.insert_one({
            "agent_name": "post_agent",
            "status": status,
            "message": message,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Failed to log action: {e}")

def get_today_reel():
    db = get_db()
    if db is None:
        return None
    try:
        # Start of day
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        reel = db.reels.find_one({
            'status': 'ready',
            'created_at': {'$gte': today_start}
        })
        return reel
    except Exception as e:
        print(f"Error fetching reel: {e}")
        return None

def format_caption(script_json: dict) -> str:
    cta = script_json.get('cta', 'Buy now!')
    hashtags = script_json.get('hashtags', '')

    mandatory_tags = "#kitchengadgets #indiankitchen #meesho #homegadgets #kitchenhacks #viralproducts #indiabuying #homehacks #desilife #affordablegadgets"

    caption = f"{cta}\nBest price link in bio!\n\n{hashtags}\n{mandatory_tags}"
    return caption

def post_to_instagram(video_url: str, caption: str) -> str:
    if not access_token or not account_id:
        raise ValueError("Instagram credentials not found.")

    graph_url = "https://graph.facebook.com/v19.0"

    # Step 1: Create media container
    print("Creating media container...")
    create_url = f"{graph_url}/{account_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token
    }

    response = requests.post(create_url, data=payload)
    response.raise_for_status()
    creation_id = response.json().get('id')

    if not creation_id:
        raise Exception("Failed to get creation_id")

    # Step 2: Poll status
    print(f"Polling status for creation_id: {creation_id}")
    status_url = f"{graph_url}/{creation_id}?fields=status_code&access_token={access_token}"

    max_retries = 3
    retry_delays = [30, 60, 120]

    for delay in retry_delays:
        time.sleep(delay)
        res = requests.get(status_url)
        res.raise_for_status()
        status = res.json().get('status_code')
        print(f"Status: {status}")

        if status == 'FINISHED':
            break
        elif status == 'ERROR':
            raise Exception("Media processing failed.")
    else:
        raise Exception("Media processing timed out.")

    # Step 3: Publish
    print("Publishing reel...")
    publish_url = f"{graph_url}/{account_id}/media_publish"
    pub_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    pub_res = requests.post(publish_url, data=pub_payload)
    pub_res.raise_for_status()

    post_id = pub_res.json().get('id')
    return post_id

def run(dry_run=False):
    print("Starting Post Agent...")
    log_agent_action("success", "Post agent started.")

    reel = get_today_reel()
    if not reel:
        log_agent_action("error", "No ready reel found for today.")
        return

    script = reel['script_json']
    caption = format_caption(script)
    video_path = reel['video_path']

    # In a real scenario, video_path needs to be a publicly accessible URL for Instagram Graph API.
    # Since it's a local file in this architecture, we would need to upload it to Supabase Storage first.
    # We will mock the upload and use a dummy URL if not actually uploading.

    # Mocking upload for the sake of the script
    video_url = f"https://example.com/{video_path}"
    print(f"Video URL for Instagram: {video_url}")
    print(f"Caption:\n{caption}")

    if dry_run:
        print("Dry run enabled, skipping Instagram post.")
        log_agent_action("success", "Dry run complete.")
        return

    try:
        post_id = post_to_instagram(video_url, caption)
        print(f"Successfully posted! ID: {post_id}")

        db = get_db()
        if db is not None:
            db.reels.update_one(
                {'_id': reel['_id']},
                {'$set': {
                    'status': 'posted',
                    'instagram_post_id': post_id,
                    'posted_at': datetime.utcnow()
                }}
            )

        log_agent_action("success", f"Posted reel successfully. ID: {post_id}")

    except Exception as e:
        log_agent_action("error", f"Failed to post to Instagram: {e}")

def run_agent(dry_run=False):
    agent = Agent(
        name="PostAgent",
        description="Posts ready video reels to Instagram.",
        instructions=["Execute the run function to post the video."],
        tools=[lambda: run(dry_run=dry_run)],
        show_tool_calls=True,
    )
    agent.print_response("Post today's video reel to Instagram.")

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    run_agent(dry_run=dry_run)