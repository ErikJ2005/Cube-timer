import streamlit as st
import pandas as pd
from datetime import datetime
import random
from PIL import Image
import magiccube

# Funksjon for å generere en tilfeldig scramble basert på kubetype
def generate_scramble(cube_type: str) -> str:
    if cube_type == "2x2":
        moves = ["R", "U", "F"]
        length = 15
    elif cube_type == "3x3":
        moves = ["R", "U", "F", "L", "D", "B"]
        length = 30
    elif cube_type in ["4x4", "5x5"]:
        moves = ["R", "U", "F", "L", "D", "B", "Rw", "Uw", "Fw", "Lw", "Dw", "Bw"]
        length = 70
    elif cube_type in ["6x6", "7x7"]:
        moves = ["R", "U", "F", "L", "D", "B", "Rw", "Uw", "Fw", "Lw", "Dw", "Bw", "3Lw", "3Uw", "3Fw", "3Lw", "3Dw", "3Bw"]
        length = 80
    scramble = []
    last_move = ""
    for _ in range(length):
        move = random.choice(moves)
        while move == last_move:
            move = random.choice(moves)
        modifier = random.choice(["", "'", "2"])
        scramble.append(move + modifier)
        last_move = move
    return " ".join(scramble)

# Funksjon for å konvertere tid-format til sekunder i desimalformat
def time_to_seconds(time_str: str) -> float:
    try:
        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            total_seconds = int(minutes) * 60 + float(seconds)
        else:
            total_seconds = float(time_str)
        return total_seconds
    except ValueError:
        st.error("Invalid time format. Use the format minutes:seconds.milliseconds.")
        return None

# Funksjon for å beregne gjennomsnittet av de siste 5 eller 12 tidene
def calculate_average(times: list, size: int) -> float:
    last_times = [time[0] for time in times[-size:]]
    if len(last_times) == size:
        return sum(last_times) / size
    return None

# Funksjon for å finne beste gjennomsnitt av 5 tider
def best_average(times: list, size: int) -> float:
    if len(times) < size:
        return None
    best_avg = float('inf')
    for i in range(len(times) - size + 1):
        current_five = [times[j][0] for j in range(i, i + size)]
        avg = sum(current_five) / size
        if avg < best_avg:
            best_avg = avg
    return best_avg

# Funksjon for å lagre tiden man skrev inn og tømme feltet igjen
def clear_text():
    st.session_state.time = st.session_state.input
    st.session_state.input = ""
    
def save_option():
    option = st.session_state.option
    st.session_state.scramble = generate_scramble(option)

# Funksjon for å vise kube bilde basert på scramble
def show_cube_image(scramble: str, size: int, pixel_size=25, border_size=1):
    # Initial kube-struktur
    cube = "W" * size * size + "O" * size * size + "G" * size * size + "R" * size * size + "B" * size * size + "Y" * size * size
    cube = magiccube.Cube(size, cube)
    cube.rotate(scramble)
    color_map = {"W": (255, 255, 255), "O": (255, 165, 0), "R": (255, 0, 0), "B": (0, 0, 255), "G": (0, 128, 0), "Y": (255, 255, 0), "⬛": (50, 50, 50)}

    cube_str = str(cube).replace(" ", "").split()
    image_width = (size * 4) * pixel_size
    image_height = (size * 3) * pixel_size
    image = Image.new("RGB", (image_width, image_height), color_map["⬛"])

    y_offset = 0
    for i, row in enumerate(cube_str):
        x_offset = size if i < size else 0
        if i >= size * 2:
            x_offset = size
        for j, facelet in enumerate(row):
            color = color_map.get(facelet, (0, 0, 0))
            for y in range(border_size, pixel_size - border_size):
                for x in range(border_size, pixel_size - border_size):
                    image.putpixel(((x_offset + j) * pixel_size + x, (y_offset + i) * pixel_size + y), color)
    return image

# Sjekker om session_state inneholder tidene for valgt kube
if "time" not in st.session_state:
    st.session_state.time = ""

if "times" not in st.session_state:
    st.session_state.times = {}

if "option" not in st.session_state:
    st.session_state.option = "3x3"

# Sørg for at det finnes en tom liste for hver kubetype
if st.session_state.option not in st.session_state.times:
    st.session_state.times[st.session_state.option] = []

st.header("Cube timer for NxN events")

col1, col2 = st.columns([0.6, 0.4])

# Valg av kube-type
st.sidebar.subheader("What cube are you solving")
option = st.sidebar.selectbox("select cube", ("2x2", "3x3", "4x4", "5x5", "6x6", "7x7"), key="option", on_change=save_option)

# Initialiser størrelsen på kuben
size = int(option[0])

# Hent tidene for valgt kube fra session_state
times = st.session_state.times.get(option, [])

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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        times.append((total_seconds, st.session_state.scramble, current_time))
        st.session_state.times[option] = times  # Oppdaterer session_state
        st.session_state.scramble = generate_scramble(option)
        
if col2.button("New scramble"):
    st.session_state.scramble = generate_scramble(option)
    
col1.write(f"Scramble for {option}: {st.session_state.scramble}")
col1.text_input(f"Write new time {option} (minutes:seconds.milliseconds):", key="input", on_change=clear_text)

# Fjern siste løsning fra session_state
if st.sidebar.button("Delete last solve") and len(times) > 0:
    times.pop(len(times)-1)
    st.session_state.times[option] = times

# Viser lagrede tider og scrambles for valgt kube
if times:
    st.sidebar.subheader(f"Saved times for {option}:")
    df = pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"])
    st.sidebar.dataframe(df)

    # Beregner og viser gjennomsnittet av de siste 5 og 12 tidene
    average_5 = calculate_average(times, 5)
    if average_5:
        col1.write(f"Current average of 5: {average_5:.2f} seconds")
    average_12 = calculate_average(times, 12)
    if average_12:
        col1.write(f"Current average of 12: {average_12:.2f} seconds")
    average_session = calculate_average(times, len(df["Tid"]))
    if average_session:
        col1.write(f"Session average: {average_session:.2f} seconds")

    # Finner beste snittet av tidene i session_state
    best_avg_5 = best_average(times, 5)
    if best_avg_5:
        col2.subheader("Best average of 5:")
        col2.write(f"{best_avg_5:.2f} seconds")
    best_avg_12 = best_average(times, 12)
    if best_avg_12:
        col2.subheader("Best average of 12:")
        col2.write(f"{best_avg_12:.2f} seconds")

# Vis bilde av kuben basert på scramble
st.write(show_cube_image(st.session_state.scramble, size))
