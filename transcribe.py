import whisper
import torch
import json
import os
import sys
import traceback

def transcribe_video(video_path, output_dir=".", duration=None):
    try:
        # Check if the video file is accessible
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file '{video_path}' does not exist.")
        
        abs_path = os.path.abspath(video_path)
        print(f"Absolute path of video file: {abs_path}")
        
        print(f"Video file '{video_path}' found.")
        
        # Print Whisper version
        print(f"Whisper version: {whisper.__version__}")
        
        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Model loaded successfully.")
        
        # Transcribe the video
        print(f"Transcribing video: {video_path}")
        
        # If duration is specified, transcribe only a portion of the video
        if duration:
            print(f"Transcribing first {duration} seconds of the video...")
            audio = whisper.load_audio(abs_path)
            audio = whisper.pad_or_trim(audio, duration * model.fps)
            result = model.transcribe(audio, word_timestamps=True)
        else:
            result = model.transcribe(abs_path, word_timestamps=True)
        
        print(f"Video Transcribed successfully.")

        # Extract transcription and timestamps
        transcription = result['text']
        segments = result['segments']

        # Validate JSON structure
        try:
            json.dumps(segments)
        except (TypeError, ValueError) as e:
            raise ValueError("Invalid JSON structure in transcription segments.") from e

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save transcription and timestamps
        output_file = os.path.join(output_dir, "transcription_with_timestamps.json")
        with open(output_file, "w") as f:
            for segment in segments:
                json.dump(segment, f, indent=2)
                f.write('\n')  # Newline for readability
                print(json.dumps(segment, indent=2))  # Log each segment for debugging
        
        print(f"Transcription saved to {output_file}")
        return segments
    except Exception as e:
        print(f"An error occurred during transcription: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.args}")
        print("Full traceback:")
        traceback.print_exc()
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_path> [output_directory] [duration_in_seconds]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else None

    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' does not exist.")
        sys.exit(1)

    transcribe_video(video_path, output_dir, duration)
