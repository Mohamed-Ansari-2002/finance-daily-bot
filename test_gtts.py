from gtts import gTTS
import os

text = "Welcome to Finance Daily. Today Sensex rose by 300 points. Nifty crossed 24,500 mark."

# tld='co.in' gives a slight Indian English accent
tts = gTTS(text=text, lang="en", tld="co.in", slow=False)

# Save as MP3
tts.save("test_voice.mp3")

print("Audio saved as test_voice.mp3")