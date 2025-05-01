import tkinter as tk
import datetime
import pyttsx3
import speech_recognition as sr
import threading
import random
import webbrowser
import math
import pywhatkit
import psutil

# === State ===
wave_active = {"user": False, "ai": False}
listening = False
favorite_song = None
stars = [{"x": random.randint(0, 1920), "y": random.randint(0, 1080),
          "size": random.randint(1, 3), "speed": random.uniform(0.3, 1.5)} for _ in range(100)]

# === Root Setup ===
root = tk.Tk()
root.title("JARVIS Interface")
root.attributes('-fullscreen', True)
root.configure(bg="black")
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
root.columnconfigure([0, 1, 2], weight=1)
root.rowconfigure(0, weight=1)

# === Background Canvas ===
background_canvas = tk.Canvas(root, bg="black", highlightthickness=0)
background_canvas.place(x=0, y=0, relwidth=1, relheight=1)

# === User Canvas ===
user_canvas = tk.Canvas(root, bg="black", highlightthickness=0)
user_canvas.grid(row=0, column=0, sticky="nsew")

# === Chat Frame ===
chat_frame = tk.Frame(root, bg="black")
chat_frame.grid(row=0, column=1, sticky="nsew")
chat_canvas = tk.Canvas(chat_frame, bg="black", highlightthickness=0)
chat_scroll = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=chat_canvas.yview, width=0)
chat_window = tk.Frame(chat_canvas, bg="black")
chat_canvas.create_window((0, 0), window=chat_window, anchor="nw")
chat_canvas.configure(yscrollcommand=chat_scroll.set)
chat_window.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))
chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# === AI Canvas ===
ai_canvas = tk.Canvas(root, bg="black", highlightthickness=0)
ai_canvas.grid(row=0, column=2, sticky="nsew")

# === TTS ===
engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    add_bubble(text, speaker="ai")
    start_wave(ai_canvas, "#ffaa00", "ai")
    engine.say(text)
    engine.runAndWait()
    stop_wave("ai")

# === Chat Bubbles ===
def add_bubble(text, speaker="user"):
    color = "#00ffee" if speaker == "user" else "#ffaa00"
    bg = "#082932" if speaker == "user" else "#331100"
    align = "w" if speaker == "user" else "e"
    label = tk.Label(chat_window, text=text, bg=bg, fg=color,
                     font=("Consolas", 10, "bold"), padx=10, pady=6,
                     wraplength=500, justify="left")
    label.pack(anchor=align, padx=20, pady=5)
    chat_canvas.yview_moveto(1.0)

# === Waveform Animation ===
def idle_wave(canvas, color, tag):
    def draw_idle(frame=0):
        canvas.delete(tag)
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        cx, cy = w // 2, h // 2
        for angle in range(0, 360, 45):
            rad = math.radians(angle + frame)
            x = cx + 40 * math.cos(rad)
            y = cy + 40 * math.sin(rad)
            canvas.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color, tags=tag)
        canvas.after(100, lambda: draw_idle(frame + 5))
    canvas.after(100, draw_idle)

def start_wave(canvas, color, who):
    wave_active[who] = True
    tag = "wave_" + who
    def draw_wave(frame=0):
        if not wave_active[who]:
            return
        canvas.delete(tag)
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        cx, cy = w // 2, h // 2
        for i in range(3):
            r = 30 + i * 20 + 5 * math.sin(math.radians(frame * 3))
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                               outline=color, width=2, tags=tag)
        canvas.after(50, lambda: draw_wave(frame + 1))
    canvas.after(100, draw_wave)

def stop_wave(who):
    wave_active[who] = False

# === Voice Input ===
def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        start_wave(user_canvas, "#00ffee", "user")
        audio = r.listen(source)
        stop_wave("user")
    try:
        query = r.recognize_google(audio)
        add_bubble(query, speaker="user")
        return query.lower()
    except:
        speak("Sorry, I didn't catch that.")
        return ""

# === Command Logic ===
def respond(query):
    global favorite_song
    if "time" in query:
        speak(datetime.datetime.now().strftime("The time is %I:%M %p"))
    elif "joke" in query:
        speak(random.choice([
            "Why don't scientists trust atoms? Because they make up everything.",
            "Why did the developer go broke? Because he used up all his cache.",
            "Why do Java developers wear glasses? Because they don't C sharp."
        ]))
    elif "play" in query and "youtube" in query:
        song = query.replace("play", "").replace("on youtube", "").strip()
        speak(f"Playing {song} on YouTube.")
        now_playing_var.set(f"🎶 Now Playing: {song}")
        pywhatkit.playonyt(song)
    elif "my favorite song is" in query:
        favorite_song = query.split("is")[-1].strip()
        speak(f"I'll remember your favorite song is {favorite_song}.")
    elif "play my favorite song" in query:
        if favorite_song:
            speak(f"Playing your favorite: {favorite_song}")
            now_playing_var.set(f"🎶 Now Playing: {favorite_song}")
            pywhatkit.playonyt(favorite_song)
        else:
            speak("You haven't told me your favorite song yet.")
    elif "exit" in query or "quit" in query:
        speak("Shutting down.")
        root.quit()
    else:
        speak("I'm not sure how to respond to that yet.")

# === MIC ===
def toggle_listening():
    global listening
    if listening:
        mic_btn.configure(bg="#222", fg="white", text="🎤")
        listening = False
    else:
        mic_btn.configure(bg="red", fg="white", text="🔴 Listening...")
        listening = True
        threading.Thread(target=run_voice, daemon=True).start()

def run_voice():
    global listening
    while listening:
        query = take_command()
        if query:
            respond(query)
        listening = False
        mic_btn.configure(bg="#222", fg="white", text="🎤")

# === Mic & Music Controls ===
mic_btn = tk.Button(root, text="🎤", font=("Consolas", 14),
                    bg="#222", fg="white", command=toggle_listening,
                    padx=20, pady=10, relief="flat")
mic_btn.place(relx=0.5, rely=0.9, anchor="center")

def play_youtube_song():
    song = yt_entry.get().strip()
    if song:
        speak(f"Playing {song} on YouTube.")
        now_playing_var.set(f"🎶 Now Playing: {song}")
        pywhatkit.playonyt(song)
    else:
        speak("Please type a song name first.")

yt_entry = tk.Entry(root, font=("Consolas", 12), width=40, bg="#111", fg="#00ffee", insertbackground="#00ffee")
yt_entry.place(relx=0.5, rely=0.95, anchor="center")

yt_button = tk.Button(root, text="▶ Play Song", font=("Consolas", 10), bg="#222", fg="white",
                      command=play_youtube_song, relief="flat")
yt_button.place(relx=0.74, rely=0.95, anchor="center")

now_playing_var = tk.StringVar()
now_playing_label = tk.Label(root, textvariable=now_playing_var,
                             font=("Consolas", 10, "bold"),
                             fg="#ffaa00", bg="black")
now_playing_label.place(relx=0.5, rely=0.98, anchor="center")

# === System Monitor ===
system_stats_var = tk.StringVar()
system_stats_label = tk.Label(root, textvariable=system_stats_var,
                              font=("Consolas", 10, "bold"),
                              fg="#00ff99", bg="black")
system_stats_label.place(relx=0.02, rely=0.97, anchor="w")

def update_system_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat = f"{battery.percent}%" if battery else "N/A"
    system_stats_var.set(f"🧠 CPU: {cpu}%   🧬 RAM: {ram}%   🔋 Battery: {bat}")
    root.after(1000, update_system_stats)

# === Labels ===
tk.Label(root, text="USER", font=("Consolas", 12, "bold"),
         fg="#00ffee", bg="black").place(relx=0.165, rely=0.85, anchor="center")
tk.Label(root, text="JARVIS", font=("Consolas", 12, "bold"),
         fg="#ffaa00", bg="black").place(relx=0.835, rely=0.85, anchor="center")

# === Background Animation ===
def animate_background(frame=0):
    background_canvas.delete("stars", "radar")
    w = background_canvas.winfo_width()
    h = background_canvas.winfo_height()
    for star in stars:
        star["y"] += star["speed"]
        if star["y"] > h:
            star["y"] = 0
            star["x"] = random.randint(0, w)
        background_canvas.create_oval(star["x"], star["y"], star["x"] + star["size"], star["y"] + star["size"],
                                      fill="#005577", outline="", tags="stars")
    cx, cy = w // 2, h // 2
    r = 120
    sweep_angle = (frame % 360)
    background_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                  outline="#003366", width=2, tags="radar")
    background_canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                 start=sweep_angle, extent=30,
                                 outline="#00ffee", width=3, style="arc", tags="radar")
    for i in range(1, 4):
        ri = i * 40
        background_canvas.create_oval(cx - ri, cy - ri, cx + ri, cy + ri,
                                      outline="#002244", width=1, tags="radar")
    background_canvas.after(60, lambda: animate_background(frame + 4))

# === Launch ===
idle_wave(user_canvas, "#00ffee", "idle_user")
idle_wave(ai_canvas, "#ffaa00", "idle_ai")
update_system_stats()
animate_background()
speak("JARVIS interface ready.")
root.mainloop()
