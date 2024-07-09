import tkinter as tk
from tkinter import scrolledtext, ttk
import ttkbootstrap as tb

def create_ui(app):
    style = tb.Style("minty")  # Apply the minty theme

    app.root.geometry("1024x768")  # Set window size to 1024x768

    # Create a frame to hold both text areas
    main_frame = tb.Frame(app.root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Configure grid layout for equal size text areas
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)

    # Create text area for displaying results (recognized speech)
    app.result_text = scrolledtext.ScrolledText(main_frame, font=("Montserrat", 12))
    app.result_text.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

    # Create text area for displaying sentiment analysis results
    app.sentiment_text = scrolledtext.ScrolledText(main_frame, font=("Montserrat", 12))
    app.sentiment_text.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

    # Create a frame for buttons and microphone dropdown
    control_frame = tb.Frame(app.root)
    control_frame.pack(pady=5, fill=tk.X)

    # Create buttons with custom purple style
    button_frame = tb.Frame(control_frame)
    button_frame.pack(pady=5, side=tk.LEFT)

    app.record_button = tb.Button(button_frame, text="Start Recording", command=app.start_recording, bootstyle="info")
    app.record_button.pack(pady=5, padx=10, side=tk.LEFT)

    app.stop_button = tb.Button(button_frame, text="Stop Recording", command=app.stop_recording, state=tk.DISABLED, bootstyle="info")
    app.stop_button.pack(pady=5, padx=10, side=tk.LEFT)

    app.analyze_button = tb.Button(button_frame, text="Analyze Text", command=app.analyze_text, bootstyle="info")
    app.analyze_button.pack(pady=5, padx=10, side=tk.LEFT)

    # Microphone selection frame to keep label and dropdown close
    mic_frame = tb.Frame(control_frame)
    mic_frame.pack(pady=5, side=tk.RIGHT)

    app.microphone_label = tb.Label(mic_frame, text="Select Microphone:", font=("Montserrat", 12))
    app.microphone_label.pack(pady=5, side=tk.LEFT)

    app.microphone_var = tk.StringVar()
    app.microphone_dropdown = ttk.Combobox(mic_frame, textvariable=app.microphone_var, font=("Montserrat", 12))
    app.microphone_dropdown.pack(pady=5, padx=(0, 10), side=tk.LEFT)
    app.microphone_dropdown['values'] = app.get_microphones()
    app.microphone_dropdown.current(0)

# Assuming the rest of your app code is here