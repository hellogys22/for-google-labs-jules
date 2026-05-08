import os
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_voiceover(text: str, output_path: str) -> str:
    """
    Call ElevenLabs API with ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID.
    Save mp3 to output_path. Return output_path.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        raise ValueError("ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID not found in environment variables.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error calling ElevenLabs API: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        raise e