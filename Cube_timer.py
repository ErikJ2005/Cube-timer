"""
- slette tekst input etter man trykker enter
- slette siste løsning
- ny scramble
- scramble endres ikke hvis man skriver feil
    - scrambel endrer seg når man endrer kuben man løser
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import random
import magiccube
from PIL import Image
 
# Funksjon for å generere en tilfeldig scramble basert på kubetype
def generate_scramble(cube_type : str) -> str:
    if cube_type == "2x2":
        moves = ["R", "U", "F"]
        length = 15
    elif cube_type == "3x3":
        moves = ["R", "U", "F", "L", "D", "B"]
        length = 30
    elif cube_type == "4x4" or cube_type == "5x5":
        moves = ["R", "U", "F", "L", "D", "B", "Rw", "Uw", "Fw", "Lw", "Dw", "Bw"]
        length = 70
    elif cube_type == "6x6" or cube_type == "7x7":
        moves = ["R", "U", "F", "L", "D", "B", "Rw", "Uw", "Fw", "Lw", "Dw", "Bw", "3Lw", "3Uw", "3Fw", "3Lw", "3Dw", "3Bw"]
        length = 80
    scramble = []
    last_move = ""
    for _ in range(length):
        move = random.choice(moves)
        while move == last_move:  # unngå å gjenta samme trekk
            move = random.choice(moves)
        modifier = random.choice(["", "'", "2"])
        scramble.append(move + modifier)
        last_move = move
    return " ".join(scramble)

from PIL import Image

def show_cube_image(scramble: str, size: int, pixel_size=25, border_size=1):
    # 3x3x3 Cube farger
    cube = "W" * size * size
    cube += "O" * size * size
    cube += "G" * size * size
    cube += "R" * size * size
    cube += "B" * size * size
    cube += "Y" * size * size

    # Rotere kuben basert på scramble
    cube = magiccube.Cube(size, cube)
    cube.rotate(scramble)

    # Fargekart for å konvertere til piksler
    color_map = {
        "W": (255, 255, 255),  # Hvit
        "O": (255, 165, 0),    # Oransje
        "R": (255, 0, 0),      # Rød
        "B": (0, 0, 255),      # Blå
        "G": (0, 128, 0),      # Grønn
        "Y": (255, 255, 0),    # Gul,
        "⬛": (50, 50, 50)      # Svart for padding
    }

    # Forbered kuben for visualisering ved å legge til mellomrom for kantene
    cube_str = str(cube)
    cube_str = cube_str.replace(" ", "").split()  # Split på linjer uten mellomrom

    # Beregn høyde og bredde for bildet (inkludert padding)
    image_width = (size * 4) * pixel_size  # Antall kolonner * pikselstørrelse
    image_height = (size * 3) * pixel_size # Antall rader * pikselstørrelse
    
    # Lag et tomt bilde
    image = Image.new("RGB", (image_width, image_height), color_map["⬛"])

    # Tegn kubens farger i bildet
    y_offset = 0  # For å holde styr på posisjon i y-retning
    for i, row in enumerate(cube_str):
        x_offset = size if i < size else 0  # Start x_offset med padding for topp
        if i >= size * 2:
            x_offset = size
        for j, facelet in enumerate(row):
            color = color_map.get(facelet, (0, 0, 0))  # Få RGB-fargen fra fargekartet
            # Tegn en rute for hver farge med kant
            for y in range(border_size, pixel_size - border_size):
                for x in range(border_size, pixel_size - border_size):
                    image.putpixel(((x_offset + j) * pixel_size + x, (y_offset + i) * pixel_size + y), color)

    return image

# Funksjon for å lagre tidene og scrambles i en CSV-fil
def save_times(cube_type : str, times : list):
    df = pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"])
    filename = f"{cube_type}_times.csv"
    df.to_csv(filename, index=False)

# Funksjon for å legge til en ny tid og scramble
def add_time(times: list, new_time: float, scramble: str) -> list:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    times.append((new_time, scramble, current_time))
    return times

# Funksjon for å laste inn eksisterende tider fra CSV-fil
def load_times(cube_type : str) -> list:
    filename = f"{cube_type}_times.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        return df.values.tolist()  # Returner en liste av lister
    return []

# Funksjon for å konvertere input fra formatet "minutter:sekunder.millisekunder" til sekunder i desimalformat
def time_to_seconds(time_str: str) -> float:
    try: # Prøver å konvertere stringen til sekunder
        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            total_seconds = int(minutes) * 60 + float(seconds)
        else:
            total_seconds = float(time_str)
        return total_seconds
    except ValueError: # Skjer hvis man skriver inn ugjyldig format
        st.error("Invalid time format. Use the format minutes:seconds.milliseconds.")
        return None

# Funksjon for å beregne gjennomsnittet av de siste 5 eller 12 tidene
def calculate_average(times : list, size :int) -> float:
    last_times = [time[0] for time in times[-size:]]
    if len(last_times) == size:
        return sum(last_times) / size
    return None

# Funksjon for å finne beste gjennomsnitt av 5 tider
def best_average(times : list, size : int) -> float:
    if len(times) < size:
        return None  # Ikke nok tider for å beregne gjennomsnitt
    best_avg = float('inf')  # Start med en uendelig høy verdi
    for i in range(len(times) - size+1):
        current_five = [times[j][0] for j in range(i, i + size)]  # Henter ut 5 tider
        avg = sum(current_five) / size
        if avg < best_avg:
            best_avg = avg
    return best_avg

# funksjon for å lagre tiden man skrev inn og tømme felte igjen
def clear_text():
    st.session_state.time = st.session_state.input
    st.session_state.input = ""
    
def save_option():
    option = st.session_state.option
    st.session_state.scramble = generate_scramble(option)

# Oppretter save og time som en session state og gjør de til tomme strings
if "time" not in st.session_state:
    st.session_state.time = ""
    
if "save" not in st.session_state:
    st.session_state.save = ""

st.header("Cube timer for NxN events")

col1, col2 = st.columns([0.6, 0.4]) #Oppretter 2 kolonner der kolonne en tar op 60% av plassen og kolonne 2 tar 40% av plassen

# Valg av kube-type
st.sidebar.subheader("What cube are you solving")
option = st.sidebar.selectbox("select cube", ("2x2", "3x3", "4x4", "5x5", "6x6", "7x7"), key="option", on_change=save_option)

if option == "2x2":
    size = 2
if option == "3x3":
    size = 3
if option == "4x4":
    size = 4
if option == "5x5":
    size = 5
if option == "6x6":
    size = 6
if option == "7x7":
    size = 7

# laster inn riktig csv fil ut i fra kuben man har valgt
times = load_times(option)

# Legger scramble til som en session state og setter den til en scramble
if "scramble" not in st.session_state:
    st.session_state.scramble = generate_scramble(option)

# Setter new_time til det man skrev inn og resetter den så den ikke har noe verdi
new_time = st.session_state.time
st.session_state.time = ""

# Legg til ny tid hvis den er gyldig
if new_time:
    total_seconds = time_to_seconds(new_time)
    if total_seconds is not None:
        times = add_time(times, total_seconds, st.session_state.scramble)
        save_times(option, times)
        st.session_state.scramble = generate_scramble(option)
        
if col2.button("New scramble"):
    st.session_state.scramble = generate_scramble(option)
    
# Skriver ut scrambelen for kuben man har valgt
col1.write(f"Scramble for {option}: {st.session_state.scramble}")

#Input der man skriver inn tid
col1.text_input(f"Write new time {option} (mintues:seconds.milliseconds):", key="input", on_change=clear_text)

#Fjerner siste tiden man la til i listen
if st.sidebar.button("Delete last solve") and len(times) > 0:
    times.pop(len(times)-1)
    save_times(option, times)

# Viser lagrede tider og scrambles for valgt kube
if times:
    st.sidebar.subheader(f"Saved times for {option}:")
    df = pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"])
    st.sidebar.dataframe(df)

    # Beregner og viser gjennomsnittet av de siste 5 og 12 tidene
    average_5 = calculate_average(times, 5)
    if average_5:
        col1.write(f"Current avrage of 5: {average_5:.2f} seconds")
    average_12 = calculate_average(times, 12)
    if average_12:
        col1.write(f"Current avrage og 12: {average_12:.2f} seconds")
    average_session = calculate_average(times, len(df["Tid"]))
    if average_session:
        col1.write(f"Session avrage: {average_session:.2f} seconds")

    #Finner beste snittet av tidene i csv filen
    best_avg_5 = best_average(times, 5)
    if best_avg_5:
        col2.subheader("Best avrage of 5:")
        col2.write(f"{best_avg_5:.2f} seconds")
    best_avg_12 = best_average(times, 12)
    if best_avg_12:
        col2.subheader("Best avrage of 12:")
        col2.write(f"{best_avg_12:.2f} seconds")


st.write(show_cube_image(st.session_state.scramble, size))

if times:
    #Lagger line chart av enkelttidene
    st.subheader("Line chart of all single times")
    st.line_chart(df["Tid"], x_label="Solves", y_label="Time (seconds)")