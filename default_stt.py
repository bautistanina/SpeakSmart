import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import ttkbootstrap as tb
import azure.cognitiveservices.speech as speechsdk
import threading
import pyaudio
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import spacy
import requests
import json
from ui import create_ui  # Import the UI creation function

# Initialize NLTK resources (uncomment if not already downloaded)
nltk.download('punkt')
nltk.download('stopwords')

# Load spaCy language model
nlp = spacy.load("en_core_web_sm")

class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SpeakSmart")

        # Initialize UI components
        create_ui(self)

        # Initialize Azure services
        self.subscription_key = "cc0a8666c9de495499d5fd54a205ad8c"
        self.endpoint = "https://speaksmart.cognitiveservices.azure.com/"
        self.region = "southeastasia"
        
        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription_key, region=self.region)
        self.speech_config.speech_recognition_language = "fil-PH"  # Set language to Filipino (Tagalog)

        # Event handlers for speech recognition
        self.speech_recognizer = None

        # Initialize threading and state
        self.recording = False
        self.recording_event = threading.Event()
        self.thread = None

    def get_microphones(self):
        p = pyaudio.PyAudio()
        mic_list = []
        for i in range(p.get_device_count()):
            mic_list.append(p.get_device_info_by_index(i).get('name'))
        p.terminate()
        return mic_list

    def get_microphone_device_id(self, mic_name):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            if p.get_device_info_by_index(i).get('name') == mic_name:
                device_id = p.get_device_info_by_index(i).get('index')
                p.terminate()
                return device_id
        p.terminate()
        return None

    def start_recording(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Listening...\n")
        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.recording = True
        self.recording_event.clear()

        # Start a new thread for streaming recognition
        self.thread = threading.Thread(target=self.stream_recognition)
        self.thread.start()

    def stop_recording(self):
        self.recording = False
        self.recording_event.set()  # Signal the thread to stop
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.speech_recognizer:
            self.speech_recognizer.stop_continuous_recognition_async().get()

    def stream_recognition(self):
        selected_mic = self.microphone_var.get()
        device_id = self.get_microphone_device_id(selected_mic)
        
        if device_id is not None:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=device_id)

            audio_input_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=audio_input_stream)
            self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

            def recognizing_callback(evt):
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, evt.result.text + "\n")
                self.result_text.see(tk.END)

            def recognized_callback(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    self.result_text.insert(tk.END, evt.result.text + "\n")
                    self.result_text.see(tk.END)
                elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                    self.result_text.insert(tk.END, "No speech could be recognized.\n")

            def canceled_callback(evt):
                self.result_text.insert(tk.END, f"Recognition canceled: {evt.reason}\n")

            self.speech_recognizer.recognizing.connect(recognizing_callback)
            self.speech_recognizer.recognized.connect(recognized_callback)
            self.speech_recognizer.canceled.connect(canceled_callback)

            self.speech_recognizer.start_continuous_recognition_async().get()

            def audio_stream():
                while not self.recording_event.is_set():
                    frames = stream.read(1024)
                    audio_input_stream.write(frames)

                audio_input_stream.close()  # Close the stream when done

            audio_thread = threading.Thread(target=audio_stream)
            audio_thread.start()

            audio_thread.join()
            self.speech_recognizer.stop_continuous_recognition_async().get()
            stream.stop_stream()
            stream.close()
            p.terminate()

        else:
            self.result_text.insert(tk.END, "Selected microphone not found.\n")
            self.record_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def analyze_text(self):
        text = self.result_text.get(1.0, tk.END).strip()

        if not text:
            self.result_text.insert(tk.END, "No text to analyze.\n")
            return

        # Tokenization with NLTK
        tokens = word_tokenize(text)
        sentences = sent_tokenize(text)

        # Stopwords removal with NLTK
        stop_words = set(stopwords.words('english'))  # Adjust for Filipino as needed
        filtered_tokens = [word for word in tokens if word.lower() not in stop_words]

        # Part-of-Speech tagging with spaCy
        doc = nlp(text)
        pos_tags = [(token.text, token.pos_) for token in doc]

        # Sentiment analysis
        sentiment = self.analyze_sentiment(text)

        # Translation to English
        translation = self.translate_text(text, "en")

        # Display results in organized manner
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)

        self.sentiment_text.delete(1.0, tk.END)
        self.sentiment_text.insert(tk.END, "=== Sentiment Analysis ===\n")
        self.sentiment_text.insert(tk.END, f"{json.dumps(sentiment, indent=2)}\n")

    def analyze_sentiment(self, text):
        path = f"{self.endpoint}/text/analytics/v3.0/sentiment"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key, "Content-Type": "application/json"}
        documents = {"documents": [{"id": "1", "language": "en", "text": text}]}
        response = requests.post(path, headers=headers, json=documents)
        sentiment = response.json()
        return sentiment

    def translate_text(self, text, to_language="en"):
        path = f"{self.endpoint}/translate?api-version=3.0&to={to_language}"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key, "Content-Type": "application/json"}
        body = [{"text": text}]
        response = requests.post(path, headers=headers, json=body)
        response_json = response.json()
        try:
            translation = response_json[0]["translations"][0]["text"]
        except (IndexError, KeyError) as e:
            translation = "Translation error: " + str(e)
        return translation

if _name_ == "_main_":
    root = tb.Window(themename="superhero")
    app = SpeechToTextApp(root)
    root.mainloop()