import streamlit as st
from google import genai
from google.genai import types
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="MarketMind Agent (1046)", layout="wide")
st.title("📈 MarketMind: Financial Research Agent")

# --- DEFINING TOOLS (Copy-pasted from your script) ---
# In a real app, you would import these from a 'tools.py' file to keep code clean.
def lookup_stock_price(ticker: str):
    """Returns the current stock price."""
    t = ticker.upper() # Clean it once
    
    # 1. Handle ALKRIE (All variations)
    if t in ["ALKRIE", "ALKRIESYS"]:
        return "$222.20"
    
    # 2. Handle GOOGLE (All variations)
    # The fix: Check against a LIST of valid aliases
    elif t in ["GOOG", "GOOGL", "GOOGLE"]: 
        return "$175.50"
        
    # 3. Handle MICROSOFT
    elif t in ["MSFT", "MICROSOFT"]:
        return "$420.00"

    return "Ticker not found. Try using the exact ticker symbol (e.g., GOOGL)."

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

def calculate_shares_from_budget(ticker: str, budget: float):
    """
    Calculates how many shares one can buy with a specific budget.
    """
    price_string = lookup_stock_price(ticker)
    if "not found" in price_string:
        return "Error: Ticker not found."
    
    clean_price = float(price_string.replace("$", ""))
    
    # The Logic the AI was missing
    num_shares = budget / clean_price
    
    return f"You can buy {num_shares:.2f} shares of {ticker} with ${budget}."

my_tools = [lookup_stock_price, get_latest_news, calculate_position_value, calculate_shares_from_budget]

# --- SESSION STATE SETUP ---
# This checks "Is this the first time running?"
if "chat_session" not in st.session_state:
    # --- PROFESSIONAL FIX: HYBRID KEY LOADING ---
    # 1. Try loading from Streamlit Cloud Secrets
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    # 2. Fallback to Local Environment (for your WSL)
    else:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        st.error("🚨 Error: API Key not found. Please set GOOGLE_API_KEY in Secrets.")
        st.stop()
        
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

                # --- BUG FIX: ESCAPE DOLLAR SIGNS ---
                # This prevents Streamlit from trying to render text as Math
                safe_text = response.text.replace("$", "\$") 

                # Show Response
                st.markdown(response.text)
                
                # Save to History
                st.session_state.messages.append({"role": "model", "content": response.text})
                
            except Exception as e:
                st.error(f"Agent Error: {e}")
