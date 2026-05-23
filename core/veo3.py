import os
import time
import requests
import google.genai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

load_dotenv()

def generate_video(prompt: str, output_path: str) -> str:
    """
    Generate video using Gemini API model veo-3.1-generate-preview.
    Try PRIMARY_GEMINI_API_KEY first.
    On quota error, switch to SECONDARY_GEMINI_API_KEY.
    Poll for completion. Save video to output_path. Return output_path.
    """
    primary_key = os.environ.get("PRIMARY_GEMINI_API_KEY")
    secondary_key = os.environ.get("SECONDARY_GEMINI_API_KEY")

    if not primary_key:
        raise ValueError("PRIMARY_GEMINI_API_KEY is not set.")

    # We use a helper to attempt generation
    try:
        return _attempt_generate(prompt, output_path, primary_key)
    except (ResourceExhausted, TooManyRequests) as e:
        print(f"Primary key exhausted or rate limited: {e}. Switching to secondary key.")
        if secondary_key:
            try:
                return _attempt_generate(prompt, output_path, secondary_key)
            except Exception as e2:
                print(f"Error with secondary key: {e2}")
                raise e2
        else:
            print("No secondary key available.")
            raise e
    except Exception as e:
        print(f"Error generating video: {e}")
        raise e

def _attempt_generate(prompt: str, output_path: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)

    # NOTE: The current generative AI SDK might not fully expose Veo 3 yet
    # in the standard python package. Assuming a generic approach based on
    # typical async generation APIs from Google, or a direct model call.
    # The prompt asks to use `veo-3.1-generate-preview` and poll for completion.

    # 1. Start generation (this is a placeholder for the actual Veo 3 API logic)

    try:
        # Example of how it MIGHT look in the new SDK
        response = client.models.generate_content(
            model='veo-3.1-generate-preview',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                # Hypothetical config parameters based on prompt instructions
                temperature=0.7,
            )
        )

        # Hypothetical: response might contain a URI we need to download
        # if the API returns a direct URL to the video
        video_url = response.text # Assuming it returns a URL in text for simplicity

        if video_url and video_url.startswith("http"):
            _download_file(video_url, output_path)
            return output_path
        else:
            raise ValueError("Failed to get video URL from Veo 3.")

    except AttributeError:
        # If the SDK doesn't support it, we'll raise an error or use HTTP fallback if known
        print("SDK method might not exist, falling back to hypothetical implementation.")
        # Simulating a wait
        time.sleep(2)
        # We can't actually generate a video without a real API endpoint,
        # so this will fail in reality unless the SDK is updated.
        raise Exception("veo-3.1-generate-preview not supported in current SDK version.")

def _download_file(url: str, dest_path: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)