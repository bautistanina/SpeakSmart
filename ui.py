import tkinter as tk
from tkinter import scrolledtext, ttk
import ttkbootstrap as tb

def create_ui(app):
    style = tb.Style("minty")  # Apply the minty theme

    app.root.geometry("1024x768")  # Set window size to 1024x768

    # Create a frame to hold the text areas and buttons
    main_frame = tb.Frame(app.root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Configure grid layout
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)
    main_frame.rowconfigure(2, weight=0)  # For the control frame

    # Create text area for displaying results (recognized speech)
    app.result_text = scrolledtext.ScrolledText(main_frame, font=("Montserrat", 12), wrap=tk.WORD)
    app.result_text.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

    # Create text area for displaying sentiment analysis results
    app.sentiment_text = scrolledtext.ScrolledText(main_frame, font=("Montserrat", 12), wrap=tk.WORD)
    app.sentiment_text.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

    # Create text area for displaying grammar suggestions
    app.grammar_text = scrolledtext.ScrolledText(main_frame, font=("Montserrat", 12), wrap=tk.WORD)
    app.grammar_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    app.grammar_text.tag_configure("suggestion", foreground="blue")

    # Create a frame for buttons and microphone dropdown
    control_frame = tb.Frame(main_frame)
    control_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

    # Create buttons with custom style
    button_frame = tb.Frame(control_frame)
    button_frame.pack(side=tk.LEFT, padx=10)

    app.record_button = tb.Button(button_frame, text="Start Recording", command=app.start_recording, bootstyle="info")
    app.record_button.pack(pady=5, side=tk.LEFT)

    app.stop_button = tb.Button(button_frame, text="Stop Recording", command=app.stop_recording, state=tk.DISABLED, bootstyle="info")
    app.stop_button.pack(pady=5, side=tk.LEFT)

    app.analyze_button = tb.Button(button_frame, text="Analyze Text", command=app.analyze_text, bootstyle="info")
    app.analyze_button.pack(pady=5, side=tk.LEFT)

    # Microphone selection frame to keep label and dropdown close
    mic_frame = tb.Frame(control_frame)
    mic_frame.pack(side=tk.RIGHT, padx=10)

    app.microphone_label = tb.Label(mic_frame, text="Select Microphone:", font=("Montserrat", 12))
    app.microphone_label.pack(side=tk.LEFT, pady=5)

    app.microphone_var = tk.StringVar()
    app.microphone_dropdown = ttk.Combobox(mic_frame, textvariable=app.microphone_var, font=("Montserrat", 12))
    app.microphone_dropdown.pack(side=tk.LEFT, pady=5)
    app.microphone_dropdown['values'] = app.get_microphones()
    app.microphone_dropdown.current(0)

    # Timer label
    app.timer_label = tb.Label(control_frame, text="Recording Time: 0 seconds", font=("Montserrat", 12))
    app.timer_label.pack(side=tk.RIGHT, padx=10, pady=5)
