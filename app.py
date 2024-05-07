import os
import psycopg2
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def connect_db():
    """Establish a connection to the database."""
    db_url = os.getenv("DATABASE_URL")
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Failed to connect to database: {e}")
        raise e

def create_tables():
    """Create database tables if they do not exist."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS trips (
            id SERIAL PRIMARY KEY,
            destination VARCHAR(255),
            departure_date DATE,
            return_date DATE,
            activities TEXT,
            accommodation VARCHAR(255),
            plan_details TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            trip_id INT REFERENCES trips(id),
            rating INT,
            comments TEXT
        );
        """
    )
    with connect_db() as conn, conn.cursor() as cur:
        for command in commands:
            cur.execute(command)
        conn.commit()

def insert_trip(destination, departure_date, return_date, activities, accommodation, plan_details):
    """Insert a new trip into the database."""
    sql = """
    INSERT INTO trips (destination, departure_date, return_date, activities, accommodation, plan_details)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute(sql, (destination, departure_date, return_date, activities, accommodation, plan_details))
        conn.commit()

def generate_content(prompt, is_chat=False):
    """Generate content using Gemini API."""
    if is_chat:
        chat_prompt = f"Answer the user's travel query: {prompt}"
        response = model.generate_content(chat_prompt)
    else:
        response = model.generate_content(prompt)
    return response.text

# Initialize tables on startup
create_tables()

# Streamlit UI setup
st.title("🏝️ AI Travel Planning")

prompt_template = """
You are an expert at planning overseas trips.

Please take the users request and plan a comprehensive trip for them.

Please include the following details:
- The destination
- The duration of the trip
- The departure and return dates
- The flight options
- The activities that will be done
- The accommodation options

The user's request is:
{prompt}
"""

# User inputs
destination = st.text_input("Destination")
departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")
activities = st.text_area("Activities you're interested in")
accommodation_preference = st.selectbox("Accommodation Preference", ["Hotel", "Hostel", "Apartment", "Other"])

if st.button("Give me a plan!"):
    full_request = f"Destination: {destination}, Departure Date: {departure_date}, Return Date: {return_date}, Activities: {activities}, Accommodation: {accommodation_preference}"
    prompt = prompt_template.format(prompt=full_request)
    reply = generate_content(prompt)
    st.write(reply)
    insert_trip(destination, departure_date, return_date, activities, accommodation_preference, reply)
    st.success("Trip saved successfully!")

# Display saved trips
if st.checkbox("Show Saved Trips"):
    st.header("Saved Trips")
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM trips")
        trips = cur.fetchall()
        if trips:
            for trip in trips:
                st.subheader(f"Trip to {trip[1]}")
                st.text(f"Dates: {trip[2]} to {trip[3]}")
                st.text(f"Activities: {trip[4]}")
                st.text(f"Accommodation: {trip[5]}")
                st.text(f"Plan Details: {trip[6]}")
        else:
            st.error("No saved trips found.")

# Chatbot interface in Streamlit
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.sidebar.title("🤖 AI Travel Assistant")
user_query = st.sidebar.text_input("Ask me anything about your trip!")

if st.sidebar.button("Ask"):
    if user_query:
        response = generate_content(user_query, is_chat=True)  # Using the existing generate_content function to integrate with Gemini
        st.session_state.chat_history.append({"user": user_query, "assistant": response})
        user_query = ""  # Clear the input after sending

# Display chat history
for chat in st.session_state.chat_history:
    st.sidebar.markdown(f"**You:** {chat['user']}")
    st.sidebar.markdown(f"**AI:** {chat['assistant']}")
