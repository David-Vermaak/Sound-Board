import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import sv_ttk
import sounddevice as sd
import pygame
from pygame import mixer, _sdl2 as devicer
import os
import shutil
import soundfile as sf
import threading

class MicrophoneThread(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.stop_event = threading.Event()

    def run(self):
        with sd.InputStream(callback=self.callback, channels=1, dtype='float32'):
            print("Microphone thread started.")
            self.stop_event.wait()

    def stop(self):
        print("Microphone thread stopped.")
        self.stop_event.set()

mixer.init()  # Initialize the mixer, this will allow the next command to work

# Returns playback devices, Boolean value determines whether they are Input or Output devices.
print("Inputs:", devicer.audio.get_audio_device_names(True))
print("Outputs:", devicer.audio.get_audio_device_names(False))

mixer.quit()  # Quit the mixer as it's initialized on your main playback device

# Initialize sound_data and microphone_thread globally
sample_rate = 44100  # Assuming 44100 Hz sample rate
sound_data = np.zeros((sample_rate * 10, 1))  # 10 seconds buffer for initialization
microphone_thread = MicrophoneThread(callback=lambda *args: None)  # Dummy callback for initialization

def microphone_callback(indata, frames, time, status):
    global sound_data
    if status:
        print(f"Error in microphone input: {status}")
        return
    # Mix the microphone input with the ongoing sound data
    indata = indata.reshape(-1, 1)
    sound_data[:frames] += indata

def mix_with_microphone(file_name):
    global sound_data, microphone_thread, sample_rate

    sound_file_directory = "user_sound_files"
    file_path = os.path.join(sound_file_directory, file_name)

    try:
        # Load the audio file
        sound_data, fs = sf.read(file_path, dtype='float32')
        if fs != sample_rate:
            raise ValueError(f"Sample rate of the audio file ({fs} Hz) does not match the expected sample rate ({sample_rate} Hz).")

        sound_data = sound_data.reshape(-1, 1)

        # Wait for the microphone thread to stop if it is running
        if microphone_thread.is_alive():
            microphone_thread.stop()
            microphone_thread.join()

        # Reset the microphone thread with the correct callback
        microphone_thread = MicrophoneThread(callback=microphone_callback)
        microphone_thread.start()

        # Initialize the mixer with the virtual cable input
        mixer.init(devicename='CABLE Input (VB-Audio Virtual Cable)')  # Use the virtual cable as output device
        mixer.music.load(file_path)
        mixer.music.play()

        while mixer.music.get_busy():
            time.sleep(1)

        mixer.music.unload()
        mixer.quit()

    except Exception as e:
        messagebox.showerror("Error", f"Unable to mix with microphone: {str(e)}")

def play_sound(file_name, mix_with_mic=True):
    try:
        if mix_with_mic:
            mix_with_microphone(file_name)
        else:
            sound_file_directory = "user_sound_files"
            file_path = os.path.join(sound_file_directory, file_name)
            # Load the audio file
            sound_data, fs = sf.read(file_path, dtype='float32')

            # Play the audio using sounddevice
            sd.play(sound_data, fs)
            sd.wait()

    except Exception as e:
        messagebox.showerror("Error", f"Unable to play sound: {str(e)}")


def display_button():
    clear_window()
    global sound_listbox, frame2

    save_button = ttk.Button(content_frame, text="Upload Sound File", command=save_sound_file, style="Accent.TButton")
    save_button.pack(pady=10)

    frame_container = ttk.Frame(content_frame)
    frame_container.pack(pady=10)

    canvas_container = tk.Canvas(frame_container, height=300)
    canvas_container.pack(side=tk.LEFT)

    frame2 = ttk.Frame(canvas_container)
    canvas_container.create_window((0, 0), window=frame2, anchor='nw')

    myscrollbar = ttk.Scrollbar(frame_container, orient="vertical", command=canvas_container.yview)
    myscrollbar.pack(side=tk.RIGHT, fill="y")
    canvas_container.configure(yscrollcommand=myscrollbar.set)


    # Load the list of sound files on application start
    load_sound_list(frame2)

def save_sound_file():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("Sound files", "*.ogg")])

    if file_path:
        sound_file_directory = "user_sound_files"
        if not os.path.exists(sound_file_directory):
            os.makedirs(sound_file_directory)

        file_name = os.path.basename(file_path)
        destination_path = os.path.join(sound_file_directory, file_name)
        shutil.copy(file_path, destination_path)

        
        # Update the sound list
        update_sound_list(file_name, frame2)

def update_sound_list(file_name, frame2):
    sound_frame = ttk.Frame(frame2)
    sound_frame.pack(pady=5, anchor='w')

    sound_label = ttk.Label(sound_frame, text=file_name)
    sound_label.pack(side=tk.LEFT)

    play_button = ttk.Button(sound_frame, text="Play", command=lambda fn=file_name: play_sound(fn))
    play_button.pack(side=tk.LEFT, padx=5)

    # Save the updated list to a text file
    save_sound_list(file_name)

def load_sound_list(frame2):
    try:
        with open("sound_list.txt", "r") as file:
            for line in file:
                sound_name = line.strip()
                update_sound_list(sound_name, frame2)
    except FileNotFoundError:
        pass  # File does not exist yet, ignore

def save_sound_list(file_name):
    with open("sound_list.txt", "a+") as file:
        file.seek(0)  # Move the cursor to the beginning of the file
        lines = file.readlines()

        # Check if the file_name is already in the list
        if file_name + '\n' not in lines:
            file.seek(0)  # Move the cursor to the beginning of the file
            file.truncate()  # Clear the contents of the file

            # Write the updated list to the file
            for line in lines:
                file.write(line)
            file.write(f"{file_name}\n")



#information textbox
def info():

    clear_window()

    title = "Program Information"
    info_text = """
        Welcome to the Sound Board
        How to Use:

        1.) Select a File: Choose a Sound File by clicking the button
        2.) After you have all of your Sound files you can play them by selecting them from the list

        

    """
    
    # Title Label
    textbox_label = ttk.Label(content_frame, text=title)
    textbox_label.pack(pady=15)
    
    frame = ttk.Frame(content_frame)
    frame.pack(fill="both", expand=False)
    
    text_area = tk.Text(frame, wrap="none", font=menu_font)
    text_area.pack(padx=15, pady=15, fill="both", expand=True)
    
    # Inserting Text which is read only
    text_area.insert(tk.INSERT, info_text)


def clear_window():
    # Destroy everything except Menu, content frame, and boolian values
    for widget in content_frame.winfo_children():
        if widget != Menu_button and widget != Info_button and widget != Exit_button and widget != content_frame:
            widget.destroy()


#stops program
def exit_program():
    # Stop the microphone thread when exiting the program
    microphone_thread.stop()
    microphone_thread.join()
    root.destroy()




#Main program config:

root = tk.Tk()

#window header title
root.title("Sound File Parser")



#setting tkinter window size (fullscreen windowed)
root.state('normal')

# Set the minimum width and height for the window
root.minsize(500, 400)


menu_font = ("Arial", 14)

# Create a style for the Menu button
menu_button_style = ttk.Style()
menu_button_style.configure("Menu.TButton", font=menu_font, foreground='white', background='#2589bd')

# Create a style for the Info button
info_button_style = ttk.Style()
info_button_style.configure("Toggle.TButton", font=menu_font, foreground='white', background='#5C946E')

# Create a style for the Exit button
exit_button_style = ttk.Style()
exit_button_style.configure("Toggle.TButton", font=menu_font, foreground='white', background='#B3001B')


# Add Main Menu button at the top left of the window
Menu_button = ttk.Button(root, text="Menu", command=display_button, style="Accent.TButton")
Menu_button.place(x=15, y=12)

# Add an Info button
Info_button = ttk.Button(root, text="Info", command=info, style="Info.TButton")
Info_button.place(x=15, y=66)  # Position below Menu_button


# Add an Exit button
Exit_button = ttk.Button(root, text="Exit", command=exit_program, style="Exit.TButton")
Exit_button.place(x=15, y=120)  # Position below Info_button


# Add a darkmode toggle switch
switch = ttk.Checkbutton(text="Light mode", style="Switch.TCheckbutton", command=sv_ttk.toggle_theme)
switch.place(x=15, y=260)  # Position below toggle switch


# Create a content frame for the main content area
content_frame = ttk.Frame(root)
content_frame.place(x=175, y=5, relwidth=.8, relheight=.95)  # Use relative dimensions for expansion


# Bind the window close event to the exit_program function
root.protocol("WM_DELETE_WINDOW", exit_program)



import ctypes as ct
#dark titlebar - ONLY WORKS IN WINDOWS 11!!
def dark_title_bar(window):
    """
    MORE INFO:
    https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
    """
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ct.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2
    value = ct.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))


dark_title_bar(root)

#trying to get the taskbar icon to work
myappid = 'Sound.File.Parser.V2' # arbitrary string
ct.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


# Theme
sv_ttk.set_theme("dark")

# Initial function
display_button()

# Initialize Pygame only once
pygame.init()

# Start the microphone thread initially
microphone_thread.start()

#this is the loop that keeps the window persistent 
root.mainloop()
