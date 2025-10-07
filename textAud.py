import pyttsx3

text = """Ugh, today was just a terrible, draining day. I'm feeling incredibly stressed about the upcoming project deadline. The team meeting went badly, and I feel like I completely failed to communicate my concerns. It was an awful experience. Now, I have to redo the entire presentation from scratch, and I'm just so anxious about it. I really feel like I'm falling behind on everything."""

engine = pyttsx3.init()
engine.save_to_file(text, 'output.wav')
engine.runAndWait()

print("Audio saved as output.wav")
