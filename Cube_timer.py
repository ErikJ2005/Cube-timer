import streamlit as st
import pandas as pd
from datetime import datetime
import random
from PIL import Image
import magiccube
from streamlit_cookies_manager import EncryptedCookieManager

# Initialize cookies with a password
password = "your_secure_password"  # Replace with a secure password
cookies = EncryptedCookieManager(prefix="cuber_timer_", password=password)

# Ensure cookies are ready
if not cookies.ready():
    st.stop()

# Function to load times from cookies
def load_times_from_cookies():
    if cookies.get("times"):
        return pd.read_json(cookies["times"])
    return pd.DataFrame(columns=["Tid", "Scramble", "Dato"])

# Function to save times to cookies
def save_times_to_cookies(times_df):
    cookies["times"] = times_df.to_json()
    cookies.save()

# Function to generate a random scramble based on cube type
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

# Function to convert time format to seconds
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

# Function to calculate average times
def calculate_average(times: list, size: int) -> float:
    last_times = [time[0] for time in times[-size:]]
    if len(last_times) == size:
        return sum(last_times) / size
    return None

# Function to find the best average of times
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

# Function to clear the input field
def clear_text():
    st.session_state.time = st.session_state.input
    st.session_state.input = ""

# Function to show cube image based on scramble
def show_cube_image(scramble: str, size: int, pixel_size=25, border_size=1):
    # Initial cube structure
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

# Initialize session state
if "time" not in st.session_state:
    st.session_state.time = ""

if "option" not in st.session_state:
    st.session_state.option = "3x3"

# Load times from cookies into session state
if "times" not in st.session_state:
    st.session_state.times = load_times_from_cookies()

# Ensure there is a list for each cube type
if st.session_state.option not in st.session_state.times:
    st.session_state.times[st.session_state.option] = []

st.header("Cube timer for NxN events")

col1, col2 = st.columns([0.6, 0.4])

# Cube type selection
st.sidebar.subheader("What cube are you solving")
option = st.sidebar.selectbox("Select cube", ("2x2", "3x3", "4x4", "5x5", "6x6", "7x7"), key="option")

# Initialize the cube size
size = int(option[0])

# Get times for the selected cube from session state
times = st.session_state.times.get(option, [])

# Set new_time to what was entered and reset
new_time = st.session_state.time
st.session_state.time = ""

# Add new time if valid
if new_time:
    total_seconds = time_to_seconds(new_time)
    if total_seconds is not None:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        times.append((total_seconds, generate_scramble(option), current_time))
        st.session_state.times[option] = times  # Update session state
        save_times_to_cookies(pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"]))

# Display the scramble
scramble = generate_scramble(option)
col1.write(f"Scramble for {option}: {scramble}")
st.text_input(f"Write new time {option} (minutes:seconds.milliseconds):", key="input", on_change=clear_text)

# Remove the last solve from session state
if st.sidebar.button("Delete last solve") and len(times) > 0:
    times.pop(len(times) - 1)
    st.session_state.times[option] = times
    save_times_to_cookies(pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"]))

# Display saved times and scrambles for the selected cube
if times:
    st.sidebar.subheader(f"Saved times for {option}:")
    df = pd.DataFrame(times, columns=["Tid", "Scramble", "Dato"])
    st.sidebar.dataframe(df)

    # Calculate and display averages
    average_5 = calculate_average(times, 5)
    if average_5:
        col1.write(f"Current average of 5: {average_5:.2f} seconds")
    average_12 = calculate_average(times, 12)
    if average_12:
        col1.write(f"Current average of 12: {average_12:.2f} seconds")
    average_session = calculate_average(times, len(df["Tid"]))
    if average_session:
        col1.write(f"Session average: {average_session:.2f} seconds")

    # Find best averages
    best_avg_5 = best_average(times, 5)
    if best_avg_5:
        col2.subheader("Best average of 5:")
        col2.write(f"{best_avg_5:.2f} seconds")
    best_avg_12 = best_average(times, 12)
    if best_avg_12:
        col2.subheader("Best average of 12:")
        col2.write(f"{best_avg_12:.2f} seconds")

# Show the cube image based on scramble
st.image(show_cube_image(scramble, size), caption="Cube Visualization")
