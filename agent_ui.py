import streamlit as st
from google import genai
from google.genai import types
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="MarketMind Agent", layout="wide")
st.title("📈 MarketMind: Financial Research Agent")

# --- DEFINING TOOLS (Copy-pasted from your script) ---
# In a real app, you would import these from a 'tools.py' file to keep code clean.
def lookup_stock_price(ticker: str):
    """Returns the current stock price."""
    # Mock data including your custom company
    if ticker.upper() == "ALKRIE":
        return "$222.20"
    elif ticker.upper() == "GOOGL":
        return "$175.50"
    return "Ticker not found."

def get_latest_news(company: str):
    """Returns latest news."""
    return f"Latest headlines for {company}: Market is bullish. CEO is optimistic."

def calculate_position_value(ticker: str, quantity: float):
    """Calculates total cost."""
    price_string = lookup_stock_price(ticker)
    if "not found" in price_string:
        return "Error: Ticker not found."
    clean_price = float(price_string.replace("$", ""))
    return f"${clean_price * quantity:,.2f}"

my_tools = [lookup_stock_price, get_latest_news, calculate_position_value]

# --- SESSION STATE SETUP ---
# This checks "Is this the first time running?"
if "chat_session" not in st.session_state:
    api_key = os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Initialize the Chat Object and store it in memory
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            tools=my_tools,
            system_instruction="You are a Financial Analyst. Use tools to answer. Be professional.",
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )
    )
    # Initialize message history for the UI display
    st.session_state.messages = []
    st.session_state.messages.append({"role": "model", "content": "MarketMind Online. Ask me about stocks or position costs."})

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- USER INPUT HANDLING ---
if prompt := st.chat_input("Ask about Alkrie, Google, or calculations..."):
    
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Process with Agent
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking & running tools..."):
            try:
                # Send to Gemini
                response = st.session_state.chat_session.send_message(prompt)
                
                # Show Response
                st.markdown(response.text)
                
                # Save to History
                st.session_state.messages.append({"role": "model", "content": response.text})
                
            except Exception as e:
                st.error(f"Agent Error: {e}")
