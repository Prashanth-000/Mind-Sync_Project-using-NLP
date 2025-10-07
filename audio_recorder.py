import sounddevice as sd
import numpy as np
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from scipy.io.wavfile import write

# Globals
fs = 44100  # Sample rate
is_recording = False
is_paused = False
audio_data = []
stream = None


def audio_callback(indata, frames, time, status):
    """This function is called automatically when new audio data is available."""
    global audio_data, is_paused
    if not is_paused:
        audio_data.append(indata.copy())


def start_recording():
    global is_recording, stream, audio_data

    if is_recording:
        messagebox.showwarning("Warning", "Already recording!")
        return

    is_recording = True
    audio_data = []

    # Start stream in a background thread
    stream = sd.InputStream(samplerate=fs, channels=1, callback=audio_callback)
    stream.start()

    status_label.config(text="Recording... 🎙️", fg="lightgreen")


def pause_recording():
    global is_paused

    if not is_recording:
        messagebox.showwarning("Warning", "Recording not started yet.")
        return

    is_paused = not is_paused
    if is_paused:
        status_label.config(text="Paused ⏸️", fg="orange")
        pause_btn.config(text="Resume")
    else:
        status_label.config(text="Recording... 🎙️", fg="lightgreen")
        pause_btn.config(text="Pause")


def stop_recording():
    global is_recording, stream

    if not is_recording:
        messagebox.showwarning("Warning", "No active recording.")
        return

    is_recording = False
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None

    status_label.config(text="Recording stopped ⏹️", fg="red")


def save_recording():
    global audio_data

    if not audio_data:
        messagebox.showwarning("Warning", "No audio data to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                             filetypes=[("WAV files", "*.wav")],
                                             title="Save Recording As")
    if file_path:
        audio_np = np.concatenate(audio_data, axis=0)
        write(file_path, fs, (audio_np * 32767).astype(np.int16))
        messagebox.showinfo("Saved", f"Recording saved successfully:\n{file_path}")


# --- GUI ---
root = tk.Tk()
root.title("🎤 Voice Recorder")
root.geometry("360x250")
root.config(bg="#1e1e1e")

tk.Label(root, text="Voice Recorder", font=("Arial", 18, "bold"), fg="white", bg="#1e1e1e").pack(pady=10)

status_label = tk.Label(root, text="Ready 🎧", fg="lightblue", bg="#1e1e1e", font=("Arial", 12))
status_label.pack(pady=10)

btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(pady=15)

start_btn = tk.Button(btn_frame, text="Start", width=10, bg="#4CAF50", fg="white", font=("Arial", 12),
                      command=start_recording)
start_btn.grid(row=0, column=0, padx=5)

pause_btn = tk.Button(btn_frame, text="Pause", width=10, bg="#FFC107", fg="black", font=("Arial", 12),
                      command=pause_recording)
pause_btn.grid(row=0, column=1, padx=5)

stop_btn = tk.Button(btn_frame, text="Stop", width=10, bg="#F44336", fg="white", font=("Arial", 12),
                     command=stop_recording)
stop_btn.grid(row=1, column=0, padx=5, pady=5)

save_btn = tk.Button(btn_frame, text="Save", width=10, bg="#2196F3", fg="white", font=("Arial", 12),
                     command=save_recording)
save_btn.grid(row=1, column=1, padx=5, pady=5)

root.mainloop()
