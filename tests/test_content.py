import unittest
from unittest.mock import patch, MagicMock
import os
import json

from agents.content_agent import generate_script
from core.elevenlabs_tts import generate_voiceover
from core.video_editor import build_reel

class TestContentAgent(unittest.TestCase):

    @patch('agents.content_agent.anthropic.Anthropic')
    @patch('agents.content_agent.anthropic_api_key', 'test_key')
    def test_claude_returns_valid_json(self, mock_anthropic):
        """Test Claude API response parsing."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        # Simulate Claude's JSON output with markdown wrappers
        mock_response.content = [MagicMock(text="```json\n{\"hook\": \"h\", \"body\": \"b\", \"cta\": \"c\", \"caption\": \"cap\", \"hashtags\": \"#h\"}\n```")]
        mock_client.messages.create.return_value = mock_response

        script = generate_script("Test Product", 100, "Meesho")

        self.assertIn('hook', script)
        self.assertIn('body', script)
        self.assertIn('cta', script)
        self.assertIn('caption', script)
        self.assertIn('hashtags', script)

    @patch('core.elevenlabs_tts.requests.post')
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test", "ELEVENLABS_VOICE_ID": "test"})
    def test_elevenlabs_returns_mp3(self, mock_post):
        """Test ElevenLabs TTS integration and file saving."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"mock audio data"]
        mock_post.return_value = mock_response

        output_path = "tests/test_output.mp3"
        try:
            res_path = generate_voiceover("Test text", output_path)
            self.assertEqual(res_path, output_path)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    @patch('core.video_editor.CompositeVideoClip')
    @patch('core.video_editor.CompositeAudioClip')
    @patch('core.video_editor.TextClip')
    @patch('core.video_editor.AudioFileClip')
    @patch('core.video_editor.VideoFileClip')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_moviepy_pipeline(self, mock_makedirs, mock_exists, mock_video, mock_audio, mock_text, mock_comp_audio, mock_composite):
        """Mock MoviePy to ensure it pieces things together without actual rendering."""
        # We mock ImageMagick text clip creation which fails if not installed
        # Since `AudioLoop` is conditionally imported inside the function, we use `patch` as a context manager inside the function if needed
        # Simple mock to verify build_reel executes fully without raising errors
        mock_exists.return_value = True

        mock_v_clip = MagicMock()
        mock_v_clip.duration = 10
        mock_v_clip.w = 1080
        mock_v_clip.h = 1920
        # Return self for chained calls
        mock_v_clip.resize.return_value = mock_v_clip
        mock_v_clip.crop.return_value = mock_v_clip
        mock_v_clip.set_audio.return_value = mock_v_clip
        mock_v_clip.set_duration.return_value = mock_v_clip
        mock_v_clip.subclip.return_value = mock_v_clip
        mock_video.return_value = mock_v_clip

        mock_a_clip = MagicMock()
        mock_a_clip.duration = 5
        mock_a_clip.volumex.return_value = mock_a_clip
        mock_audio.return_value = mock_a_clip

        mock_comp_audio_instance = MagicMock()
        mock_comp_audio_instance.set_duration.return_value = mock_comp_audio_instance
        mock_comp_audio.return_value = mock_comp_audio_instance

        mock_comp_clip = MagicMock()
        mock_composite.return_value = mock_comp_clip

        mock_text_instance = MagicMock()
        mock_text_instance.set_position.return_value = mock_text_instance
        mock_text_instance.set_duration.return_value = mock_text_instance
        mock_text_instance.set_start.return_value = mock_text_instance
        mock_text.return_value = mock_text_instance

        output_path = "tests/test_reel.mp4"

        with patch('moviepy.audio.fx.AudioLoop') as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.apply.return_value = mock_a_clip
            mock_loop.return_value = mock_loop_instance

            build_reel("dummy_v.mp4", "dummy_a.mp3", "hook", "cta", output_path)

        self.assertTrue(mock_comp_clip.write_videofile.called)

if __name__ == '__main__':
    unittest.main()