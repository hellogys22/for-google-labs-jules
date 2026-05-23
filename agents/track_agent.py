import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from agno.agent import Agent

from core.db import get_db
from core.notifier import send_telegram

load_dotenv()

def log_agent_action(status: str, message: str):
    db = get_db()
    if db is None:
        print(f"Log (local): {status} - {message}")
        return
    try:
        db.agent_logs.insert_one({
            "agent_name": "track_agent",
            "status": status,
            "message": message,
            "created_at": datetime.utcnow()
        })
    except Exception as e:
        print(f"Failed to log action: {e}")

def scrape_affiliate_dashboard(platform: str, email: str, password: str) -> dict:
    print(f"Scraping dashboard for {platform}...")
    # Real scraping placeholder:
    try:
        # with sync_playwright() as p:
        #     browser = p.chromium.launch()
        #     page = browser.new_page()
        #     ... navigate to dashboard, login with email/password, extract metrics
        pass
    except Exception as e:
        print(f"Error scraping {platform} dashboard: {e}")

    # We return mock metrics because real affiliate dashboards have captchas and bot protections
    # that would block automated non-configured headless browsers in this generic script.
    if platform == "meesho":
        return {"clicks": 1500, "conversions": 30, "commission_inr": 800}
    elif platform == "deodap":
        return {"clicks": 500, "conversions": 10, "commission_inr": 300}
    return {"clicks": 0, "conversions": 0, "commission_inr": 0}

def get_todays_reel():
    db = get_db()
    if db is None:
        return None
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        reel = db.reels.find_one({
            'status': 'posted',
            'posted_at': {'$gte': today_start}
        })
        return reel
    except Exception as e:
        print(f"Error fetching today's reel: {e}")
        return None

def run():
    print("Starting Track Agent...")
    log_agent_action("success", "Track agent started.")

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    total_clicks = 0
    total_conversions = 0
    total_commission = 0

    try:
        # 1 & 2: Scrape Dashboards
        platforms = [
            ("meesho", os.environ.get("MEESHO_AFFILIATE_EMAIL"), os.environ.get("MEESHO_AFFILIATE_PASSWORD")),
            ("deodap", os.environ.get("DEODAP_AFFILIATE_EMAIL"), os.environ.get("DEODAP_AFFILIATE_PASSWORD"))
        ]

        for platform, email, pwd in platforms:
            if not email:
                continue

            data = scrape_affiliate_dashboard(platform, email, pwd)
            total_clicks += data['clicks']
            total_conversions += data['conversions']
            total_commission += data['commission_inr']

            # 3. Store in earnings table
            db = get_db()
            if db is not None:
                db.earnings.insert_one({
                    'date': today_str,
                    'platform': platform,
                    'clicks': data['clicks'],
                    'conversions': data['conversions'],
                    'commission_inr': data['commission_inr'],
                    'created_at': datetime.utcnow()
                })

    except Exception as e:
        log_agent_action("error", f"Failed scraping dashboards: {e}")
        return

    # 4. Update performance score for today's product
    try:
        reel = get_todays_reel()
        db = get_db()
        if reel and db is not None:
            product_id = reel['product_id']

            conversion_rate = total_conversions / total_clicks if total_clicks > 0 else 0

            # Fetch current score
            product = db.products.find_one({'id': product_id})
            if product:
                current_score = product.get('performance_score', 0.5)
                new_score = current_score

                if conversion_rate > 0.05:
                    new_score = min(1.0, current_score + 0.1)
                elif conversion_rate < 0.01:
                    new_score = max(0.0, current_score - 0.05)

                db.products.update_one({'id': product_id}, {'$set': {'performance_score': new_score}})
                print(f"Updated performance score for product {product_id} to {new_score}")
    except Exception as e:
        log_agent_action("error", f"Failed updating performance score: {e}")

    # 5. Insert into daily_reports table
    try:
        db = get_db()
        if db is not None:
            db.daily_reports.insert_one({
                'date': today_str,
                'total_clicks': total_clicks,
                'total_conversions': total_conversions,
                'total_commission_inr': total_commission,
                'best_product': "placeholder_best", # Would need logic to determine
                'worst_product': "placeholder_worst",
                'created_at': datetime.utcnow()
            })
    except Exception as e:
        log_agent_action("error", f"Failed saving daily report: {e}")

    # 6. Telegram notification
    if total_commission > 1000:
        msg = f"Today's earnings: INR {total_commission} | Clicks: {total_clicks} | Conversions: {total_conversions}"
        send_telegram(msg)

    log_agent_action("success", "Track agent finished successfully.")
    print("Track Agent Finished.")

def run_agent():
    agent = Agent(
        name="TrackAgent",
        description="Tracks affiliate earnings and updates the database.",
        instructions=["Execute the run function to start tracking."],
        tools=[run]
    )
    agent.print_response("Track today's affiliate dashboard earnings.")

if __name__ == "__main__":
    run_agent()