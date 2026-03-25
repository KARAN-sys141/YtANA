from youtube_transcript_api import YouTubeTranscriptApi

video_id = "M7FIvfx5J10" # Google ka video, isme captions pakka hain

print(f"Testing Transcript for {video_id}...")

try:
    # Sabse simple method try karte hain
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("\nSUCCESS! Transcript found:")
    print(transcript[0]) # Pehli line print karo
except Exception as e:
    print("\nFAILED!")
    print(f"Error: {e}")