import os
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv

from core.rag import search_products
from core.elevenlabs_tts import generate_voiceover
from core.video_editor import build_reel, build_slideshow
from core.veo3 import generate_video
from agno.agent import Agent
from core.db import get_db

load_dotenv()

anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

def log_agent_action(status: str, message: str):
    db = get_db()
    if db is None:
        print(f"Log (local): {status} - {message}")
        return
    try:
        db.agent_logs.insert_one({
            "agent_name": "content_agent",
            "status": status,
            "message": message,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Failed to log action: {e}")

def generate_script(product_name: str, price: float, platform: str) -> dict:
    if not anthropic_api_key:
        # Mock script for testing
        return {
            "hook": f"Wait! Check out this {product_name}!",
            "body": f"Only for {price} rupees on {platform}. It will change your life.",
            "cta": "Link in bio to buy now!",
            "caption": "The best kitchen gadget you will ever find.",
            "hashtags": "#kitchengadgets #viral"
        }

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    system_prompt = (
        "You are a viral Instagram Reels scriptwriter for Indian Home & Kitchen gadgets. "
        "Write short punchy Hindi/Hinglish scripts. Always start with a scroll-stopping hook. "
        "Include a product demo description in the body. End with a strong CTA. "
        "Respond ONLY in valid JSON with these exact keys: hook, body, cta, caption, hashtags"
    )

    user_message = f"Product: {product_name}, Price: {price} INR, Platform: {platform}"

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Ensure we parse JSON
        content = response.content[0].text
        # Sometimes Claude puts markdown around it
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())
    except Exception as e:
        print(f"Error generating script: {e}")
        raise e

def run():
    print("Starting Content Agent...")
    log_agent_action("success", "Content agent started.")

    # 1. RAG query
    try:
        products = search_products("best viral Home Kitchen gadget under 500 rupees India high conversion", match_count=1)
        if not products:
            log_agent_action("error", "No products found in RAG search.")
            return

        product = products[0]
        product_id = product['id']
        product_name = product['name']
        price = product['price']
        platform = product['platform']
        image_url = product.get('image_url')

    except Exception as e:
        log_agent_action("error", f"RAG search failed: {e}")
        return

    # 2. Generate script
    try:
        script = generate_script(product_name, price, platform)
    except Exception as e:
        log_agent_action("error", f"Script generation failed: {e}")
        return

    # 3. Generate voiceover
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    audio_path = f"audio/voiceover_{product_id}_{today_str}.mp3"
    full_text = f"{script['hook']} {script['body']} {script['cta']}"

    try:
        generate_voiceover(full_text, audio_path)
    except Exception as e:
        log_agent_action("error", f"Voiceover generation failed: {e}")
        # Create dummy audio file for testing
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, 'wb') as f: f.write(b"")
        # return

    # 4. Video Logic
    output_path = f"videos/final/reel_{product_id}_{today_str}.mp4"
    raw_path = f"videos/raw/{product_id}.mp4"
    gen_path = f"videos/raw/{product_id}_generated.mp4"
    img_path = f"videos/raw/{product_id}.jpg"

    video_generated = False

    try:
        if os.path.exists(raw_path):
            # Try to build with raw path
            try:
                build_reel(raw_path, audio_path, script['hook'], script['cta'], output_path)
                video_generated = True
            except Exception as e:
                print(f"Failed to build with raw video: {e}")

        if not video_generated:
            # Try Veo 3
            print("Attempting to generate video with Veo 3...")
            try:
                prompt = f"Product showcase video for {product_name}, 9:16 vertical, studio lighting, Indian kitchen background, satisfying demo, no text"
                generate_video(prompt, gen_path)
                build_reel(gen_path, audio_path, script['hook'], script['cta'], output_path)
                video_generated = True
            except Exception as e:
                print(f"Veo 3 generation failed: {e}")

        if not video_generated and image_url:
            # Fallback to slideshow
            print("Falling back to slideshow...")
            import requests
            try:
                img_data = requests.get(image_url).content
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                with open(img_path, 'wb') as handler:
                    handler.write(img_data)

                # Mock a dummy audio if elevenlabs failed but we still want to test
                if not os.path.exists(audio_path):
                    with open(audio_path, 'wb') as f: f.write(b"")

                build_slideshow(img_path, audio_path, script['hook'], script['cta'], output_path)
                video_generated = True
            except Exception as e:
                print(f"Slideshow generation failed: {e}")

        if not video_generated:
            raise Exception("All video generation methods failed.")

    except Exception as e:
        log_agent_action("error", f"Video pipeline failed: {e}")
        return

    # 5. Save to MongoDB
    db = get_db()
    if db is not None:
        try:
            db.reels.insert_one({
                'product_id': product_id,
                'script_json': script,
                'video_path': output_path,
                'audio_path': audio_path,
                'status': 'ready',
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            log_agent_action("error", f"Failed to save reel metadata: {e}")
            return

    log_agent_action("success", "Content agent finished successfully.")
    print("Content Agent Finished.")

def run_agent():
    agent = Agent(
        name="ContentAgent",
        description="Generates scripts and video reels based on top products.",
        instructions=["Execute the run function to start the content generation process."],
        tools=[run]
    )
    agent.print_response("Generate today's video reel.")

if __name__ == "__main__":
    run_agent()