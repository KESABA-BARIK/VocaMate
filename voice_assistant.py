import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime

# Set API key
GOOGLE_API_KEY = "GOOGLE_API_KEY"
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

app_commands = {
    "browser": ["open browser", "launch browser", "start browser", "i want to browse", "open chrome"],
    "notepad": ["open notepad", "write notes", "text editor", "launch notepad"],
    "calculator": ["open calculator", "start calculator", "do some math", "open calc"],
    "cmd": ["open command prompt", "open terminal", "launch cmd"],
    "explorer": ["open file explorer", "open explorer", "show my files"],
    "vscode": ["open vs code", "open code", "launch vs code", "open vs"],
}

app_actions = {
    "browser": lambda: os.system("start chrome"),
    "notepad": lambda: os.system("notepad"),
    "calculator": lambda: os.system("calc"),
    "cmd": lambda: os.system("start cmd"),
    "explorer": lambda: os.system("explorer"),
    "vscode": lambda: os.system("code")
}


class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')

        # Initialize TTS engine
        self.engine = pyttsx3.init()
        self.is_listening = False
        self.is_speaking = False

        # Configure TTS voice
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
        self.engine.setProperty('rate', 180)

        self.setup_ui()

    def setup_ui(self):
        # Create main canvas and scrollbar for scrolling
        canvas = tk.Canvas(self.root, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1e1e1e')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", pady=20)

        # Main container (now inside scrollable frame)
        main_frame = tk.Frame(scrollable_frame, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=(0, 20))

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Title
        title_label = tk.Label(main_frame, text="AI Voice Assistant",
                               font=('Arial', 24, 'bold'),
                               fg='#00d4aa', bg='#1e1e1e')
        title_label.pack(pady=(0, 20))

        # Status frame
        status_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', bd=2)
        status_frame.pack(fill='x', pady=(0, 20))

        self.status_label = tk.Label(status_frame, text="Ready",
                                     font=('Arial', 14, 'bold'),
                                     fg='#00ff00', bg='#2d2d2d')
        self.status_label.pack(pady=10)

        # Control buttons frame
        controls_frame = tk.Frame(main_frame, bg='#1e1e1e')
        controls_frame.pack(pady=(0, 20))

        # Listen button
        self.listen_btn = tk.Button(controls_frame, text="Start Listening",
                                    font=('Arial', 12, 'bold'),
                                    bg='#00d4aa', fg='white',
                                    activebackground='#00b89c',
                                    padx=20, pady=10,
                                    command=self.toggle_listening)
        self.listen_btn.pack(side='left', padx=(0, 10))

        # Clear button
        clear_btn = tk.Button(controls_frame, text="Clear Chat",
                              font=('Arial', 12, 'bold'),
                              bg='#ff6b6b', fg='white',
                              activebackground='#ff5252',
                              padx=20, pady=10,
                              command=self.clear_chat)
        clear_btn.pack(side='left', padx=10)

        # Settings button
        settings_btn = tk.Button(controls_frame, text="Settings",
                                 font=('Arial', 12, 'bold'),
                                 bg='#4dabf7', fg='white',
                                 activebackground='#339af0',
                                 padx=20, pady=10,
                                 command=self.show_settings)
        settings_btn.pack(side='left', padx=(10, 0))

        # Chat display
        chat_frame = tk.Frame(main_frame, bg='#1e1e1e')
        chat_frame.pack(fill='x', pady=(0, 20))

        chat_label = tk.Label(chat_frame, text="Conversation",
                              font=('Arial', 14, 'bold'),
                              fg='#ffffff', bg='#1e1e1e')
        chat_label.pack(anchor='w', pady=(0, 10))

        self.chat_display = scrolledtext.ScrolledText(chat_frame,
                                                      font=('Arial', 11),
                                                      bg='#2d2d2d', fg='#ffffff',
                                                      insertbackground='#ffffff',
                                                      selectbackground='#4dabf7',
                                                      wrap='word',
                                                      height=15)
        self.chat_display.pack(fill='x')

        # Quick actions frame
        actions_frame = tk.Frame(main_frame, bg='#1e1e1e')
        actions_frame.pack(fill='x', pady=(20, 20))

        actions_label = tk.Label(actions_frame, text="Quick Actions",
                                 font=('Arial', 12, 'bold'),
                                 fg='#ffffff', bg='#1e1e1e')
        actions_label.pack(anchor='w', pady=(0, 10))

        # Quick action buttons
        quick_actions_frame = tk.Frame(actions_frame, bg='#1e1e1e')
        quick_actions_frame.pack(fill='x')

        quick_buttons = [
            ("Browser", lambda: self.execute_app_action("browser")),
            ("Notepad", lambda: self.execute_app_action("notepad")),
            ("Calculator", lambda: self.execute_app_action("calculator")),
            ("VS Code", lambda: self.execute_app_action("vscode")),
            ("Explorer", lambda: self.execute_app_action("explorer"))
        ]

        for i, (text, command) in enumerate(quick_buttons):
            btn = tk.Button(quick_actions_frame, text=text,
                            font=('Arial', 10),
                            bg='#495057', fg='white',
                            activebackground='#6c757d',
                            padx=15, pady=8,
                            command=command)
            btn.pack(side='left', padx=5, pady=10)

        # Add some bottom padding to ensure everything is visible
        bottom_spacer = tk.Frame(main_frame, bg='#1e1e1e', height=50)
        bottom_spacer.pack(fill='x')

        # Initial welcome message
        self.add_message("Assistant",
                         "Hello! I am your AI voice assistant. Click 'Start Listening' or use quick actions to get started!",
                         "#00d4aa")

    def add_message(self, sender, message, color="#ffffff"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_display.see(tk.END)

        # Color the sender name
        start_idx = self.chat_display.index(tk.END + "-2c linestart")
        end_idx = f"{start_idx}+{len(timestamp) + len(sender) + 4}c"
        self.chat_display.tag_add(sender, start_idx, end_idx)
        self.chat_display.tag_config(sender, foreground=color, font=('Arial', 11, 'bold'))

    def update_status(self, status, color="#ffffff"):
        self.status_label.config(text=status, fg=color)
        self.root.update()

    def speak(self, text):
        self.is_speaking = True
        self.update_status("Speaking...", "#ffd43b")
        self.engine.say(text)
        self.engine.runAndWait()
        self.is_speaking = False
        if not self.is_listening:
            self.update_status("Ready", "#00ff00")

    def listen(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.update_status("Listening...", "#ff6b6b")
            try:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return ""

        try:
            self.update_status("Processing...", "#ffd43b")
            text = recognizer.recognize_google(audio)
            return text.lower()
        except sr.UnknownValueError:
            self.add_message("System", "Sorry, I didn't catch that.", "#ff6b6b")
            return ""
        except sr.RequestError:
            self.add_message("System", "Sorry, network error.", "#ff6b6b")
            return ""

    def ask_ai(self, prompt):
        try:
            self.update_status("Thinking...", "#4dabf7")
            response = model.generate_content(f"Please provide a concise response (max 100 words): {prompt}")
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return "There was an error getting a response from Gemini."

    def execute_app_action(self, app_name):
        self.add_message("You", f"Launch {app_name}", "#4dabf7")
        try:
            app_actions[app_name]()
            self.add_message("Assistant", f"{app_name.title()} launched successfully!", "#00d4aa")
            threading.Thread(target=lambda: self.speak(f"{app_name} launched"), daemon=True).start()
        except Exception as e:
            error_msg = f"Failed to launch {app_name}: {str(e)}"
            self.add_message("System", error_msg, "#ff6b6b")

    def process_command(self, command):
        if not command:
            return

        self.add_message("You", command, "#4dabf7")

        if "exit" in command or "quit" in command:
            self.add_message("Assistant", "Goodbye!", "#00d4aa")
            threading.Thread(target=lambda: self.speak("Goodbye!"), daemon=True).start()
            self.root.after(2000, self.root.quit)
            return

        # Check for app commands
        matched = False
        for app, keywords in app_commands.items():
            for keyword in keywords:
                if keyword in command:
                    self.execute_app_action(app)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            # Ask AI
            ai_response = self.ask_ai(command)
            if ai_response:
                self.add_message("Assistant", ai_response, "#00d4aa")
                threading.Thread(target=lambda: self.speak(ai_response), daemon=True).start()

    def listening_loop(self):
        while self.is_listening:
            if not self.is_speaking:
                command = self.listen()
                if command:
                    self.process_command(command)
            time.sleep(0.1)

    def toggle_listening(self):
        if self.is_listening:
            self.is_listening = False
            self.listen_btn.config(text="Start Listening", bg="#00d4aa")
            self.update_status("Ready", "#00ff00")
        else:
            self.is_listening = True
            self.listen_btn.config(text="Stop Listening", bg="#ff6b6b")
            threading.Thread(target=self.listening_loop, daemon=True).start()

    def clear_chat(self):
        self.chat_display.delete(1.0, tk.END)
        self.add_message("System", "Chat cleared", "#ffd43b")

    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#1e1e1e')

        tk.Label(settings_window, text="Voice Assistant Settings",
                 font=('Arial', 16, 'bold'),
                 fg='#00d4aa', bg='#1e1e1e').pack(pady=20)

        # Voice settings
        voice_frame = tk.Frame(settings_window, bg='#2d2d2d', relief='raised', bd=2)
        voice_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(voice_frame, text="Voice Settings",
                 font=('Arial', 12, 'bold'),
                 fg='#ffffff', bg='#2d2d2d').pack(pady=10)

        # Speech rate
        rate_frame = tk.Frame(voice_frame, bg='#2d2d2d')
        rate_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(rate_frame, text="Speech Rate:",
                 fg='#ffffff', bg='#2d2d2d').pack(side='left')

        rate_var = tk.IntVar(value=180)
        rate_scale = tk.Scale(rate_frame, from_=100, to=300,
                              orient='horizontal', variable=rate_var,
                              bg='#2d2d2d', fg='#ffffff',
                              troughcolor='#4dabf7')
        rate_scale.pack(side='right', fill='x', expand=True, padx=10)

        def update_rate():
            self.engine.setProperty('rate', rate_var.get())

        tk.Button(voice_frame, text="Apply Changes",
                  command=update_rate,
                  bg='#00d4aa', fg='white',
                  padx=20, pady=5).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop()