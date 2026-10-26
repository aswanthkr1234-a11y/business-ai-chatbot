
import os
import pandas as pd
import streamlit as st  # pyright: ignore[reportMissingImports]
import sqlite3
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
from google import genai

# Load settings from the .env file
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Configure the webpage

st.set_page_config(
    page_title="Business AI Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
    }

    [data-testid="stChatInput"] {
        border-radius: 12px;
    }

    h1 {
        font-weight: 700;
    }

    .stButton button {
        border-radius: 10px;
        min-height: 42px;
    }
</style>
""", unsafe_allow_html=True)

# Business settings
st.sidebar.title("⚙️ Business Settings")

business_name = st.sidebar.text_input(
    "Business name",
    value="BrightPath Coaching Centre"
)

st.title(f"💬 {business_name}")
st.caption("Your virtual customer support assistant")

st.info(
    "Welcome! 👋 Ask me about our services, prices, "
    "or opening hours."
)

st.write("**Quick questions**")

col1, col2, col3 = st.columns(3)

if col1.button("💰 View prices", use_container_width=True):
    st.session_state["quick_question"] = "What are your prices?"

if col2.button("🕒 Opening hours", use_container_width=True):
    st.session_state["quick_question"] = "What are your opening hours?"

if col3.button("📋 Our services", use_container_width=True):
    st.session_state["quick_question"] = "What services do you offer?"

st.caption("Your virtual customer support assistant")


business_location = st.sidebar.text_input(
    "Business location",
    value="Kannur, Kerala"
)

business_services = st.sidebar.text_area(
    "Services and prices",
    value="Python Course: Rs. 5000\nWeb Development: Rs. 7000\nData Science: Rs. 9000"
)

business_hours = st.sidebar.text_input(
    "Opening hours",
    value="Monday to Saturday, 9 AM to 6 PM"
)

BUSINESS_INFO = f"""
Business name: {business_name}
Location: {business_location}

Services and prices:
{business_services}

Opening hours: {business_hours}
"""


# Check whether the API key exists
if not API_KEY:
    st.error(
        "API key missing. Please check your .env file."
    )
    st.stop()

# Create the Gemini API client
client = genai.Client(api_key=API_KEY)

# Store chat history during the current session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get a new question from the customer

question = st.session_state.pop("quick_question", None)

typed_question = st.chat_input(
    "Ask about services, prices or timings..."
)

if typed_question:
    question = typed_question


if question:
    # Display the customer's question
    st.chat_message("user").markdown(question)

    # Add question to chat history
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Keep recent messages for context
    recent_messages = st.session_state.messages[-8:]

    conversation = "\n".join(
        f'{msg["role"]}: {msg["content"]}'
        for msg in recent_messages
    )

    prompt = f"""
You are a helpful customer support assistant.

BUSINESS INFORMATION:
{BUSINESS_INFO}

RULES:
1. Answer using only the business information.
2. Never invent prices, policies or contact details.
3. If information is missing, say you don't know.
4. Be polite and keep answers easy to understand.

CONVERSATION:
{conversation}

Write the next assistant response.
"""

    # Generate an answer using Gemini
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

                answer = response.text

                if not answer:
                    answer = "Sorry, I couldn't generate an answer."

            st.markdown(answer)

        except Exception as error:
            answer = (
                "Sorry, something went wrong. "
                "Check your API configuration and try again."
            )
            st.error(answer)

            # Show technical details for debugging
            with st.expander("Technical error details"):
                st.code(str(error))

    # Save the answer in chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# Clear the conversation
if st.session_state.messages:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()



# Customer enquiry form
st.divider()
st.subheader("📩 Contact Us")

with st.form("customer_enquiry_form"):
    customer_name = st.text_input("Name")
    customer_email = st.text_input("Email")
    customer_enquiry = st.text_area("Enquiry")
    submitted = st.form_submit_button("Submit")

if submitted:
        if not customer_name.strip() or not customer_email.strip() or not customer_enquiry.strip():
            st.warning("Please fill in all fields.")

        elif "@" not in customer_email or "." not in customer_email:
            st.warning("Please enter a valid email address.")

        else:
            try:
                conn = sqlite3.connect("business_enquiries.db")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO enquiries (name, email, enquiry)
                    VALUES (?, ?, ?)
                    """,
                    (
                        customer_name.strip(),
                        customer_email.strip(),
                        customer_enquiry.strip()
                    )
                )

                conn.commit()
                conn.close()

                st.success("Your enquiry has been saved successfully!")

            except sqlite3.Error as error:
                st.error("Unable to save your enquiry.")
                st.error(str(error))




# Create the database and enquiries table
def init_database():
    conn = sqlite3.connect("business_enquiries.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            enquiry TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_database()



# Admin Dashboard
st.divider()
st.header("🔐 Admin Dashboard")

admin_password = st.text_input(
    "Enter admin password",
    type="password",
    key="admin_password"
)

if st.button("View Enquiries"):
    if admin_password != os.getenv("ADMIN_PASSWORD", "admin123"):
        st.error("Incorrect password. Please try again.")

    else:
        try:
            conn = sqlite3.connect("business_enquiries.db")

            enquiries = pd.read_sql_query(
                """
                SELECT id, name, email, enquiry, created_at
                FROM enquiries
                ORDER BY id DESC
                """,
                conn
            )

            conn.close()

            if enquiries.empty:
                st.info("No customer enquiries found.")

            else:
                st.success(f"Total enquiries: {len(enquiries)}")
                st.dataframe(enquiries, use_container_width=True)

                csv_data = enquiries.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="📥 Download Enquiries as CSV",
                    data=csv_data,
                    file_name="customer_enquiries.csv",
                    mime="text/csv"
                )

        except Exception as error:
            st.error("Unable to load enquiries.")
            st.code(str(error))


