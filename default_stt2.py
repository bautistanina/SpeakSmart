import tkinter as tk
from tkinter import scrolledtext, messagebox
import azure.cognitiveservices.speech as speechsdk
import threading
import pyaudio
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import spacy
import requests
import json
from ui import create_ui
from textstat import flesch_reading_ease, flesch_kincaid_grade
import time

# Initialize NLTK resources
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
            self.root.after(1000, self.update_timer)
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

        # Tokenization with NLTK
        tokens = word_tokenize(text)
        sentences = sent_tokenize(text)

        # Stopwords removal with NLTK
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word.lower() not in stop_words]

        # Part-of-Speech tagging with spaCy
        doc = nlp(text)
        pos_tags = [(token.text, token.pos_) for token in doc]

        # Sentiment analysis
        sentiment = self.analyze_sentiment(text)

        # Grammar check
        grammar_errors = self.check_grammar(text)

        # Readability score
        readability = self.calculate_readability(text)

        # Passive voice detection
        passive_voice = self.detect_passive_voice(doc)

        # Pronunciation feedback
        pronunciation_feedback = self.check_pronunciation(tokens)

        # Display results in organized manner
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)

        # Detailed feedback
        self.sentiment_text.delete(1.0, tk.END)
        self.sentiment_text.insert(tk.END, "=== Sentiment Analysis ===\n")
        self.sentiment_text.insert(tk.END, f"Overall Sentiment: {sentiment['documents'][0]['sentiment']}\n")
        self.sentiment_text.insert(tk.END, "Confidence Scores:\n")
        for score in sentiment['documents'][0]['confidenceScores']:
            self.sentiment_text.insert(tk.END, f"{score.capitalize()}: {sentiment['documents'][0]['confidenceScores'][score]:.2f}\n")

        self.sentiment_text.insert(tk.END, "\n=== Analysis Feedback ===\n")
        self.sentiment_text.insert(tk.END, self.generate_feedback(tokens, filtered_tokens, pos_tags, sentiment, grammar_errors, readability, passive_voice, pronunciation_feedback))

    def generate_feedback(self, tokens, filtered_tokens, pos_tags, sentiment, grammar_errors, readability, passive_voice, pronunciation_feedback):
        feedback = []

        # Clarity: Check for filler words and repetition
        filler_words = {"uh", "um", "like", "you know", "so", "actually", "basically"}
        fillers_used = [word for word in tokens if word.lower() in filler_words]
        if fillers_used:
            feedback.append(f"Try to reduce the use of filler words like: {', '.join(set(fillers_used))}.")

        # Coherence: Check sentence length and complexity
        sentence_lengths = [len(sentence.split()) for sentence in sent_tokenize(' '.join(tokens))]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
        if avg_sentence_length > 20:
            feedback.append(f"Your sentences are quite long (average {avg_sentence_length:.1f} words). Try to make them shorter and more concise for better clarity.")

        # Vocabulary: Check for diverse vocabulary usage
        unique_tokens = set(filtered_tokens)
        if len(unique_tokens) / len(tokens) < 0.5:
            feedback.append("Consider using a more diverse vocabulary to make your speech more engaging.")

        # Sentiment: Provide feedback based on sentiment analysis
        overall_sentiment = sentiment['documents'][0]['sentiment']
        if overall_sentiment == "positive":
            feedback.append("Your speech has a positive tone. Keep up the positive energy!")
        elif overall_sentiment == "negative":
            feedback.append("Your speech has a negative tone. Try to incorporate more positive elements.")
        else:
            feedback.append("Your speech has a neutral tone. Consider adding more emotion to engage your audience.")

        # Grammar: Feedback on grammar errors
        if grammar_errors:
            feedback.append(f"Grammar errors detected: {', '.join(grammar_errors)}. Consider revising these parts.")

        # Readability: Feedback based on readability score
        if readability['flesch'] < 60:
            feedback.append("Your speech is somewhat difficult to read. Simplifying your sentences might help.")
        if readability['fk_grade'] > 8:
            feedback.append("Your speech is at a higher grade level. Consider using simpler words for better comprehension.")

        # Passive Voice: Feedback on passive voice usage
        if passive_voice:
            feedback.append(f"Consider reducing passive voice usage: {'; '.join(passive_voice)}.")

        # Pronunciation: Feedback on pronunciation (if any issues detected)
        if pronunciation_feedback:
            feedback.append(f"Pronunciation issues detected with: {'; '.join(pronunciation_feedback)}.")

        return "\n".join(feedback)

    def check_grammar(self, text):
        # Integrate a grammar checking API like Grammarly or LanguageTool
        grammar_errors = []  # Placeholder implementation
        return grammar_errors

    def calculate_readability(self, text):
        flesch = flesch_reading_ease(text)
        fk_grade = flesch_kincaid_grade(text)
        return {"flesch": flesch, "fk_grade": fk_grade}

    def detect_passive_voice(self, doc):
        passive_sentences = [sent.text for sent in doc.sents if any(token.dep_ in ("nsubjpass", "auxpass") for token in sent)]
        return passive_sentences

    def check_pronunciation(self, tokens):
        # Implement pronunciation checking feature
        pronunciation_issues = []  # Placeholder implementation
        return pronunciation_issues

    def analyze_sentiment(self, text):
        path = f"{self.endpoint}/text/analytics/v3.0/sentiment"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key, "Content-Type": "application/json"}
        body = {"documents": [{"id": "1", "language": "en", "text": text}]}
        response = requests.post(path, headers=headers, json=body)
        return response.json()

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()
