import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib
import pandas as pd
from datetime import timedelta

# --- DATABASE CONFIGURATION (for XAMPP) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default XAMPP password is empty
    'database': 'tm'
}

# --- DATABASE SETUP ---

# Function to connect to the MySQL database
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL Database: {e}")
        return None

# Function to create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    if conn is None:
        return
    # Use a dictionary cursor to access columns by name
    c = conn.cursor(dictionary=True)
    
    # Admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS AdminData (
            username VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB;
    ''')
    # Event table
    c.execute('''
        CREATE TABLE IF NOT EXISTS EventData (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            date DATE NOT NULL,
            time TIME NOT NULL,
            venue VARCHAR(255) NOT NULL,
            description TEXT
        ) ENGINE=InnoDB;
    ''')
    # Ticket booking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS TicketBookData (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            user_name VARCHAR(255) NOT NULL,
            user_phone VARCHAR(255) NOT NULL,
            FOREIGN KEY (event_name) REFERENCES EventData (name) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    ''')
    conn.commit()
    c.close()
    conn.close()

# --- HELPER FUNCTIONS ---

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# --- ADMIN FUNCTIONS (MySQL Version) ---

def add_admin(username, password):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    try:
        # MySQL uses %s as a placeholder
        c.execute('INSERT INTO AdminData (username, password) VALUES (%s, %s)', (username, make_hashes(password)))
        conn.commit()
        st.success("Admin account created successfully!")
    except Error as err:
        # Error 1062 is for duplicate entry
        if err.errno == 1062:
            st.warning("Username already exists.")
        else:
            st.error(f"Database Error: {err}")
    finally:
        c.close()
        conn.close()

def login_admin(username, password):
    conn = get_db_connection()
    if conn is None: return False
    c = conn.cursor(dictionary=True) # Dictionary cursor is important here
    c.execute('SELECT password FROM AdminData WHERE username = %s', (username,))
    data = c.fetchone()
    c.close()
    conn.close()
    if data:
        return check_hashes(password, data['password'])
    return False

# --- EVENT FUNCTIONS (MySQL Version) ---

def add_event(name, date, time, venue, description):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    try:
        c.execute('INSERT INTO EventData (name, date, time, venue, description) VALUES (%s, %s, %s, %s, %s)',
                  (name, date, time, venue, description))
        conn.commit()
        st.success(f"Event '{name}' added successfully!")
    except Error as err:
        if err.errno == 1062:
            st.error(f"Error: An event with the name '{name}' already exists.")
        else:
            st.error(f"Database Error: {err}")
    finally:
        c.close()
        conn.close()

def get_all_events():
    conn = get_db_connection()
    if conn is None: return []
    c = conn.cursor(dictionary=True)
    c.execute('SELECT * FROM EventData ORDER BY date, time')
    events = c.fetchall()
    c.close()
    conn.close()
    return events

def delete_event(event_name):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    c.execute('DELETE FROM EventData WHERE name = %s', (event_name,))
    # The ON DELETE CASCADE in the table definition will handle ticket deletion automatically
    conn.commit()
    c.close()
    conn.close()
    st.success(f"Event '{event_name}' and all its bookings have been deleted.")

def get_booking_count(event_name):
    conn = get_db_connection()
    if conn is None: return 0
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM TicketBookData WHERE event_name = %s', (event_name,))
    count = c.fetchone()[0]
    c.close()
    conn.close()
    return count
    
def get_bookings_for_event(event_name):
    conn = get_db_connection()
    if conn is None: return []
    c = conn.cursor(dictionary=True)
    c.execute('SELECT user_name, user_phone FROM TicketBookData WHERE event_name = %s', (event_name,))
    bookings = c.fetchall()
    c.close()
    conn.close()
    return bookings

    book

# --- TICKET BOOKING FUNCTIONS (MySQL Version) ---

def book_ticket(event_name, user_name, user_phone):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    c.execute('INSERT INTO TicketBookData (event_name, user_name, user_phone) VALUES (%s, %s, %s)',
              (event_name, user_name, user_phone))
    conn.commit()
    c.close()
    conn.close()
    st.success(f"Ticket booked for {user_name} for the event '{event_name}'!")

# --- STREAMLIT UI (No changes needed here) ---

st.set_page_config(page_title="EventPro", layout="wide")

def admin_page():
    st.title("Admin Panel")

    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        choice = st.selectbox("Login / Sign Up", ["Login", "Sign Up"])

        if choice == "Login":
            st.subheader("Admin Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                if login_admin(username, password):
                    st.session_state.admin_logged_in = True
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
        else:
            st.subheader("Create New Admin Account")
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type='password')
            if st.button("Sign Up"):
                if new_username and new_password:
                    add_admin(new_username, new_password)
                else:
                    st.warning("Please enter both username and password.")

    else:
        st.success("You are logged in as an Admin.")
        
        st.header("Admin Dashboard")

        with st.expander("➕ Add New Event"):
            with st.form("add_event_form", clear_on_submit=True):
                event_name = st.text_input("Event Name")
                col1, col2 = st.columns(2)
                with col1:
                    event_date = st.date_input("Event Date")
                with col2:
                    event_time = st.time_input("Event Time")
                event_venue = st.text_input("Venue")
                event_description = st.text_area("Description")
                
                submitted = st.form_submit_button("Add Event")
                if submitted:
                    if event_name and event_date and event_time and event_venue:
                        add_event(event_name, str(event_date), str(event_time), event_venue, event_description)
                    else:
                        st.warning("Please fill in all required fields: Name, Date, Time, and Venue.")

        st.markdown("---")
        
        st.header("📊 Manage Events")
        all_events = get_all_events()
        if not all_events:
            st.info("No events have been added yet.")
        else:
            event_names = [event['name'] for event in all_events]
            
            event_data = []
            for event in all_events:
                count = get_booking_count(event['name'])
                event_data.append({
                    "Event Name": event['name'],
                    "Date": event['date'],
                    "Time": event['time'],
                    "Venue": event['venue'],
                    "Tickets Booked": count
                })
            
            st.table(pd.DataFrame(event_data))

            st.subheader("🗑️ Delete an Event")
            event_to_delete = st.selectbox("Select Event to Delete", options=event_names)
            if st.button("Delete Event", key=f"delete_{event_to_delete}"):
                delete_event(event_to_delete)
                st.rerun()
            
            st.markdown("---")
            st.subheader("🎟️ View Ticket Bookings")
            if event_names:
                event_to_view = st.selectbox("Select an Event to see Bookings", options=event_names, key="view_bookings")
                
                if event_to_view:
                    bookings = get_bookings_for_event(event_to_view)
                    if bookings:
                        booking_df = pd.DataFrame(bookings)
                        booking_df.rename(columns={"user_name": "Booked By (Name)", "user_phone": "Phone Number"}, inplace=True)
                        st.dataframe(booking_df)
                    else:
                        st.info(f"No tickets have been booked for '{event_to_view}' yet.")

        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()


def events_page():
    st.title("🎉 Upcoming Events")
    st.markdown("Browse our events and book your tickets now!")
    
    all_events = get_all_events()

    if not all_events:
        st.info("There are no upcoming events at the moment. Please check back later!")
        return

    cols = st.columns(3)
    for i, event in enumerate(all_events):
        with cols[i % 3]:
            with st.container():
                st.subheader(event['name'])
                st.markdown(f"**📍 Venue:** {event['venue']}")
                
                # --- Fix for DATE ---
                st.markdown(f"**📅 Date:** {pd.to_datetime(event['date']).strftime('%A, %d %B %Y')}")

                # --- Fix for TIME ---
                event_time = event['time']
                if isinstance(event_time, timedelta):  # MySQL TIME comes as timedelta
                    total_seconds = int(event_time.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    formatted_time = f"{hours:02}:{minutes:02}"
                else:
                    formatted_time = str(event_time)

                st.markdown(f"**⏰ Time:** {pd.to_datetime(formatted_time).strftime('%I:%M %p')}")



                if event['description']:
                    st.markdown(f"**📝 About:** {event['description']}")
                
                with st.expander("Book Your Ticket"):
                    with st.form(key=f"book_form_{event['id']}", clear_on_submit=True):
                        user_name = st.text_input("Your Name", key=f"name_{event['id']}")
                        user_phone = st.text_input("Your Phone Number", key=f"phone_{event['id']}")
                        
                        book_button = st.form_submit_button(label="Confirm Booking")
                        
                        if book_button:
                            if user_name and user_phone:
                                book_ticket(event['name'], user_name, user_phone)
                            else:
                                st.warning("Please enter your name and phone number.")
            st.markdown("---")


def main():
    create_tables()
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Events", "Admin"])

    if page == "Admin":
        admin_page()
    else:
        events_page()

if __name__ == '__main__':
    main()