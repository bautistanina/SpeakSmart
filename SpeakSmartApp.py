import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import font as tkfont
import azure.cognitiveservices.speech as speechsdk
import threading
import pyaudio
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import spacy
import requests
import json
import language_tool_python
from transformers import pipeline
from sklearn.feature_extraction.text import CountVectorizer
from textstat import flesch_reading_ease, flesch_kincaid_grade
import time
from APIClient import GroqClient
import ttkbootstrap as tb
from UserInterface import create_ui


# Initialize NLTK resources
# nltk.download('punkt')
# nltk.download('stopwords')

# Load spaCy language model
nlp = spacy.load("en_core_web_sm")

# Initialize summarizer and emotion classifier
summarizer = pipeline("summarization")
emotion_classifier = pipeline("sentiment-analysis", model="bhadresh-savani/distilbert-base-uncased-emotion")

import tkinter as tk
from tkinter import font as tkfont

class StartupPage(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent, bg="white")
        self.parent = parent
        self.app = app

        # Custom fonts
        title_font = tkfont.Font(family="Montserrat", size=48, weight="bold")
        desc_font = tkfont.Font(family="Montserrat", size=18)
        button_font = tkfont.Font(family="Montserrat", size=16, weight="bold")
        
        # Load logo image
        self.logo_image = tk.PhotoImage(file="logo.png") 

        # Logo label
        self.logo_label = tk.Label(self, image=self.logo_image, bg="white")
        self.logo_label.pack(pady=40)

        # App title
        self.title_label = tk.Label(self, text="SpeakSmart", font=title_font, fg="#2c3e50", bg="white")
        self.title_label.pack(pady=10)

        # App description
        self.description_label = tk.Label(
            self,
            text="Your advanced speech-to-text and NLP analysis tool",
            wraplength=600,
            justify="center",
            font=desc_font,
            fg="#34495e",
            bg="white"
        )
        self.description_label.pack(pady=30)

        # Start button
        self.start_button = tk.Button(
            self,
            text="Get Started",
            command=self.start_app,
            font=button_font,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief="flat",
            padx=30,
            pady=15,
            cursor="hand2"
        )
        self.start_button.pack(pady=50)

        # Hover effect
        self.start_button.bind("<Enter>", self.on_enter)
        self.start_button.bind("<Leave>", self.on_leave)

    def start_app(self):
        self.pack_forget()
        self.app.show_main_app()

    def on_enter(self, e):
        self.start_button['background'] = '#2980b9'

    def on_leave(self, e):
        self.start_button['background'] = '#3498db'
        
class SpeechToTextApp(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.groq_client = GroqClient()

        # Initialize UI components
        create_ui(self)

        # Initialize Azure services
        self.subscription_key = "cc0a8666c9de495499d5fd54a205ad8c"
        self.endpoint = "https://speaksmart.cognitiveservices.azure.com/"
        self.region = "southeastasia"

        # Initialize speech config
        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription_key, region=self.region)
        self.speech_config.speech_recognition_language = "en-US"  # Set language to English

        # Event handlers for speech recognition
        self.speech_recognizer = None

        # Initialize threading and state
        self.recording = False
        self.recording_event = threading.Event()
        self.thread = None

        # Timer and text storage
        self.start_time = None
        self.recognized_text = []

    def get_microphones(self):
        p = pyaudio.PyAudio()
        mic_list = [p.get_device_info_by_index(i).get('name') for i in range(p.get_device_count())]
        p.terminate()
        return mic_list

    def get_microphone_device_id(self, mic_name):
        p = pyaudio.PyAudio()
        device_id = None
        for i in range(p.get_device_count()):
            if p.get_device_info_by_index(i).get('name') == mic_name:
                device_id = p.get_device_info_by_index(i).get('index')
                break
        p.terminate()
        return device_id

    def start_recording(self):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Listening...\n")
        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.recording = True
        self.recording_event.clear()
        self.recognized_text.clear()

        # Start a new thread for streaming recognition
        self.thread = threading.Thread(target=self.stream_recognition)
        self.thread.start()

        # Start timer
        self.start_time = time.time()
        self.update_timer()

    def stop_recording(self):
        self.recording = False
        self.recording_event.set()
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.speech_recognizer:
            self.speech_recognizer.stop_continuous_recognition_async().get()

        # Display all recognized text
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, " ".join(self.recognized_text))

    def update_timer(self):
        if self.recording:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Recording Time: {elapsed_time} seconds")
            self.parent.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="Recording stopped.")

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
                    self.recognized_text.append(evt.result.text)
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

                audio_input_stream.close()

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

        # Sentiment analysis (keep this part)
        sentiment = self.analyze_sentiment(text)

        # Display results in organized manner
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)

        # Analysis feedback
        self.sentiment_text.delete(1.0, tk.END)

        # Configure tags
        self.sentiment_text.tag_configure("bold", font=("Montserrat", 18, "bold"))
        self.sentiment_text.tag_configure("center", justify="center")

        # Insert and style titles
        self.sentiment_text.insert(tk.END, "Sentiment Analysis\n", ("bold", "left"))
        self.sentiment_text.insert(tk.END, f"Overall Sentiment: {sentiment['documents'][0]['sentiment']}\n")
        self.sentiment_text.insert(tk.END, "Confidence Scores:\n")
        for score in sentiment['documents'][0]['confidenceScores']:
            self.sentiment_text.insert(tk.END, f"{score.capitalize()}: {sentiment['documents'][0]['confidenceScores'][score]:.2f}\n")

       
        # Replace the content of the grammar_text with Groq analysis
        self.grammar_text.delete(1.0, tk.END)
        self.grammar_text.tag_configure("bold", font=("Montserrat", 18, "bold"))
        self.grammar_text.tag_configure("center", justify="center")
        self.grammar_text.insert(tk.END, "✨ SpeakSmart with AI ✨\n\n", ("bold", "center"))
        groq_analysis = self.groq_client.check_grammar(text)
        self.grammar_text.insert(tk.END, groq_analysis)

        self.grammar_text.insert(tk.END, "\n\nFeedback Analysis\n\n", ("bold", "center"))

        # Use Groq client for feedback
        groq_feedback = self.groq_client.analyze_feedback(text)
        self.grammar_text.insert(tk.END, groq_feedback)

        self.grammar_text.insert(tk.END, "\n\nSpeech Analysis\n\n", ("bold", "center"))

         # Use Groq client for speech
        groq_speech = self.groq_client.analyze_speech(text)
        self.grammar_text.insert(tk.END, groq_speech)

        self.grammar_text.insert(tk.END, "\n\nTone Suggestion\n\n", ("bold", "center"))

         # Use Groq client for tone suggestion
        groq_sug = self.groq_client.suggest_tone(text)
        self.grammar_text.insert(tk.END, groq_sug)

        self.grammar_text.insert(tk.END, "\n\n Over All Suggestion\n\n", ("bold", "center"))

         # Use Groq client for tone suggestion
        groq_osug = self.groq_client.get_suggestions(text)
        self.grammar_text.insert(tk.END, groq_osug)


        # Additional NLP analysis
        entities = self.extract_entities(text)
        summary = self.summarize_text(text)
        emotions = self.detect_emotions(text)
        keywords = self.extract_keywords(text)

        # Display additional analyses
        self.sentiment_text.insert(tk.END, "\nEntities\n", ("bold", "left"))
        for entity in entities:
            self.sentiment_text.insert(tk.END, f"{entity[0]}: {entity[1]}\n")

        self.sentiment_text.insert(tk.END, "\nSummary\n", ("bold", "left"))
        self.sentiment_text.insert(tk.END, summary)

        self.sentiment_text.insert(tk.END, "\n\nEmotions\n", ("bold", "left"))
        for emotion in emotions:
            self.sentiment_text.insert(tk.END, f"{emotion['label']}: {emotion['score']:.2f}\n")

        self.sentiment_text.insert(tk.END, "\nKeywords\n", ("bold", "left"))
        self.sentiment_text.insert(tk.END, ", ".join(keywords))

    def analyze_sentiment(self, text):
        url = f"{self.endpoint}/text/analytics/v3.1/sentiment"
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json"
        }
        documents = {"documents": [{"id": "1", "language": "en", "text": text}]}
        response = requests.post(url, headers=headers, json=documents)
        return response.json()

    def extract_entities(self, text):
        doc = nlp(text)
        entities = [(entity.text, entity.label_) for entity in doc.ents]
        return entities

    def summarize_text(self, text):
        summary = summarizer(text, max_length=150, min_length=25, do_sample=False)
        return summary[0]['summary_text']

    def detect_emotions(self, text):
        emotions = emotion_classifier(text)
        return emotions

    def extract_keywords(self, text, num_keywords=5):
        vectorizer = CountVectorizer(stop_words='english', max_features=num_keywords)
        X = vectorizer.fit_transform([text])
        keywords = vectorizer.get_feature_names_out()
        return keywords
    
    def clear_all_text(self):
        self.result_text.delete(1.0, tk.END)
        self.sentiment_text.delete(1.0, tk.END)
        self.grammar_text.delete(1.0, tk.END)

    def show_main_app(self):
        self.pack(expand=True, fill='both')

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("SpeakSmart")

        self.startup_page = StartupPage(self, self)
        self.startup_page.pack(expand=True, fill='both')

        self.main_app = SpeechToTextApp(self)

        # Make the windowed fullscreen
        self.state('zoomed')  # This will maximize the window
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))

    def show_main_app(self):
        self.main_app.show_main_app()

if __name__ == "__main__":
    app = Application()
    app.mainloop()