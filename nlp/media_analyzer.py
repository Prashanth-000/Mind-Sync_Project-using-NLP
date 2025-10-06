import whisper
import soundfile as sf
import numpy as np
import librosa

# Load model once
whisper_model = whisper.load_model("base")

def transcribe_audio_local(audio_file_path):
    try:
        if not audio_file_path.lower().endswith(".wav"):
            print("ERROR: Only WAV files supported without ffmpeg.")
            return ""

        # Read WAV
        audio, sr = sf.read(audio_file_path)

        # Convert stereo -> mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # Resample to 16kHz
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        # Convert to float32 (Whisper expects float32)
        audio = np.asarray(audio, dtype=np.float32)

        # Whisper requires 1D array
        if audio.ndim != 1:
            audio = audio.flatten()

        print(f"DEBUG: audio dtype={audio.dtype}, shape={audio.shape}")

        # Transcribe using numpy array (force dtype float32)
        result = whisper_model.transcribe(audio)
        return result.get("text", "")

    except Exception as e:
        print(f"ERROR during Whisper transcription: {e}")
        return ""
