import os
from groq import Groq
from tkinter import messagebox

class GroqClient:
    def __init__(self):
        self.api_key = "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"
        self.client = Groq(api_key=self.api_key)
        self.context = []

    def chat_completion(self, messages):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model="mixtral-8x7b-32768",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            messagebox.showerror("API Error", f"Error accessing Groq API: {e}")
            return None

    def update_context(self, role, content):
        self.context.append({
            "role": role,
            "content": content,
        })

    def check_grammar(self, text):
        self.update_context("user", f"Check the grammar and provide suggestions for improvement in the following text make the first sentence as the revised perfect grammar text: {text}")
        return self.chat_completion(self.context)

    def analyze_speech(self, text):
        self.update_context("user", f"Analyze the following speech and provide feedback on clarity, coherence, and overall effectiveness: {text}")
        return self.chat_completion(self.context)

    def suggest_tone(self, text):
        self.update_context("user", f"Analyze the tone of the following text and provide suggestions for improvement: {text}")
        return self.chat_completion(self.context)

    def analyze_feedback(self, text):
        self.update_context("user", f"Provide a comprehensive analysis of the following speech, including feedback on content, delivery, and areas for improvement: {text}")
        return self.chat_completion(self.context)

    def get_suggestions(self, text):
        self.update_context("user", f"Provide detailed suggestions : {text}")
        return self.chat_completion(self.context)

# Example usage:
if __name__ == "__main__":
    client = GroqClient()

    text = "This is an example text for grammar checking."
    grammar_suggestions = client.check_grammar(text)
    print("Grammar Suggestions:", grammar_suggestions)

    feedback_analysis = client.analyze_feedback(text)
    print("Feedback Analysis:", feedback_analysis)

    tone_suggestions = client.suggest_tone(text)
    print("Tone Suggestions:", tone_suggestions)

    improvement_suggestions = client.get_suggestions(text)
    print("Suggestions for Improvement:", improvement_suggestions)