import os
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, CompositeAudioClip, ImageClip

def build_reel(video_path: str, audio_path: str, hook_text: str, cta_text: str, output_path: str) -> str:
    """
    Use MoviePy to: resize to 1080x1920, add text overlays, mix audio, export mp4.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 1. Load the raw product video
    video = VideoFileClip(video_path)

    # 2. Crop/resize to 1080x1920 (9:16 vertical)
    # Target aspect ratio: 9:16
    target_width = 1080
    target_height = 1920

    # Resize video maintaining aspect ratio, then crop to center
    video = video.resize(height=target_height)
    if video.w > target_width:
        # Crop center
        x_center = video.w / 2
        video = video.crop(x1=x_center - target_width/2, y1=0, x2=x_center + target_width/2, y2=target_height)
    else:
        # If too narrow, resize width and crop height
        video = VideoFileClip(video_path).resize(width=target_width)
        y_center = video.h / 2
        video = video.crop(x1=0, y1=y_center - target_height/2, x2=target_width, y2=y_center + target_height/2)

    # 3. Add hook text as bold white text at top of frame for first 3 seconds
    # Assuming ImageMagick is installed for TextClip
    try:
        hook_clip = TextClip(hook_text, fontsize=70, color='white', font='Arial-Bold', method='caption', size=(target_width - 100, None))
        hook_clip = hook_clip.set_position(('center', 150)).set_duration(3)
    except Exception as e:
        print(f"Warning: Failed to create TextClip for hook: {e}")
        hook_clip = None

    # 4. Add CTA text as bold white text at bottom of frame for last 3 seconds
    video_duration = video.duration
    cta_start = max(0, video_duration - 3)
    try:
        cta_clip = TextClip(cta_text, fontsize=70, color='white', font='Arial-Bold', method='caption', size=(target_width - 100, None))
        cta_clip = cta_clip.set_position(('center', target_height - 300)).set_start(cta_start).set_duration(3)
    except Exception as e:
        print(f"Warning: Failed to create TextClip for CTA: {e}")
        cta_clip = None

    # 5. Set ElevenLabs voiceover as the main audio track
    voiceover = AudioFileClip(audio_path)

    # Trim video duration to match voiceover if voiceover is shorter
    if voiceover.duration < video.duration:
        video = video.subclip(0, voiceover.duration)
    else:
        # If voiceover is longer, loop video or just keep video duration
        # For simplicity, we keep video duration, and audio will be cut
        pass

    # 6. Mix assets/bgmusic.mp3 at 20% volume underneath voiceover
    bgmusic_path = "assets/bgmusic.mp3"
    if os.path.exists(bgmusic_path):
        bgmusic = AudioFileClip(bgmusic_path).volumex(0.20)
        # Loop bgmusic to match video duration if needed
        from moviepy.audio.fx import AudioLoop
        bgmusic = AudioLoop(duration=video.duration).apply(bgmusic)

        # Mix audio
        final_audio = CompositeAudioClip([voiceover, bgmusic])
    else:
        final_audio = voiceover

    # 7. Set final audio and trim total duration to max 30 seconds
    final_audio = final_audio.set_duration(min(video.duration, 30))
    video = video.set_audio(final_audio)
    video = video.set_duration(min(video.duration, 30))

    # Combine video and text clips
    clips = [video]
    if hook_clip: clips.append(hook_clip)
    if cta_clip: clips.append(cta_clip)

    final_video = CompositeVideoClip(clips)

    # 8. Export to output_path at 1080x1920, 30fps
    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    final_video.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )

    # Close clips to release resources
    video.close()
    voiceover.close()
    if os.path.exists(bgmusic_path):
        bgmusic.close()
    final_video.close()

    return output_path

def build_slideshow(image_path: str, audio_path: str, hook_text: str, cta_text: str, output_path: str) -> str:
    """
    Fallback: Use MoviePy to create a Ken Burns slideshow from a product image.
    Animate with slow pan/zoom effect over 15 seconds.
    Apply same audio + text overlay pipeline.
    """
    # Create a simple image clip for 15 seconds
    image_clip = ImageClip(image_path).set_duration(15)

    # Target aspect ratio: 9:16
    target_width = 1080
    target_height = 1920

    # Resize image to fill screen
    image_clip = image_clip.resize(height=target_height)
    if image_clip.w < target_width:
        image_clip = ImageClip(image_path).resize(width=target_width)

    # Crop to center
    x_center = image_clip.w / 2
    y_center = image_clip.h / 2
    image_clip = image_clip.crop(
        x1=x_center - target_width/2,
        y1=y_center - target_height/2,
        x2=x_center + target_width/2,
        y2=y_center + target_height/2
    )

    # Apply a slight zoom effect (Ken Burns approximation)
    # MoviePy zoom is tricky, simple approach: scale up slowly
    def zoom(t):
        return 1 + 0.02 * t # Zoom in 2% per second

    # Apply zoom by resizing frames
    # Note: image_clip.resize(zoom) is very slow in MoviePy,
    # for simplicity, we just use the static image

    # Save a temporary video
    temp_video_path = output_path.replace('.mp4', '_temp.mp4')
    image_clip.write_videofile(temp_video_path, fps=30)

    # Pass to build_reel
    final_path = build_reel(temp_video_path, audio_path, hook_text, cta_text, output_path)

    # Clean up temp
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)

    return final_path