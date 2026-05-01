import streamlit as st
from google import genai
from google.genai import types
import os
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="MarketMind Agent (1046)", layout="wide")
st.title("📈 MarketMind: Financial Research Agent")

with st.expander("💡 About this Demo:"):
    st.markdown("""
    This application demonstrates **Agentic Tool Use** and the **ReAct Pattern** (Reason + Act).
    
    Unlike standard chatbots that hallucinate numbers, this Agent detects specific intents (Stock Price, Calculation) and executes **Python Functions (Tools)** to get the exact answer. It combines the fluency of an LLM with the precision of a calculator.
    
    **Role:** Engineered the "Toolbox" (Stock Lookup, Budget Calculator) and the Python logic that handles input sanitization (e.g., mapping "Alkriesys" to "ALKRIE"), proving how to build robust, deterministic AI agents.
    """)

# --- DEFINING TOOLS (Copy-pasted from your script) ---
# In a real app, you would import these from a 'tools.py' file to keep code clean.
def lookup_stock_price(ticker: str):
    """Returns the current real-time stock price."""
    try:
        t = ticker.upper()
        # Handle your custom aliases
        aliases = {
            "ALKRIE": "GOOGL",  # Map to real ticker for demo
            "ALKRIESYS": "GOOGL",
            "GOOGLE": "GOOGL",
            "MICROSOFT": "MSFT",
        }
        t = aliases.get(t, t)
        stock = yf.Ticker(t)
        price = stock.fast_info["last_price"]
        return f"${price:.2f}"
    except Exception as e:
        return f"Ticker not found: {e}"

def get_latest_news(company: str):
    """Returns latest real news headlines for a company."""
    try:
        t = company.upper()
        aliases = {"GOOGLE": "GOOGL", "MICROSOFT": "MSFT"}
        t = aliases.get(t, t)
        stock = yf.Ticker(t)
        news = stock.news[:3]  # Get top 3 headlines
        if not news:
            return "No recent news found."
        headlines = "\n".join(
            [f"- {n['content']['title']}" for n in news]
        )
        return f"Latest news for {company}:\n{headlines}"
    except Exception as e:
        return f"Error fetching news: {e}"

def get_company_info(ticker: str):
    """Returns key company details like sector, employees, description."""
    try:
        t = ticker.upper()
        aliases = {"GOOGLE": "GOOGL", "MICROSOFT": "MSFT"}
        t = aliases.get(t, t)
        stock = yf.Ticker(t)
        info = stock.info
        return (
            f"**{info.get('longName', t)}**\n"
            f"- Sector: {info.get('sector', 'N/A')}\n"
            f"- Industry: {info.get('industry', 'N/A')}\n"
            f"- Employees: {info.get('fullTimeEmployees', 'N/A'):,}\n"
            f"- Market Cap: ${info.get('marketCap', 0)/1e9:.2f}B\n"
            f"- 52W High: ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"- 52W Low: ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"- Summary: {info.get('longBusinessSummary', 'N/A')[:200]}..."
        )
    except Exception as e:
        return f"Error fetching company info: {e}"

def calculate_position_value(ticker: str, quantity: float):
    """Calculates total cost."""
    aliases = {"GOOGLE": "GOOGL", "MICROSOFT": "MSFT", "ALKRIE": "GOOGL"}
    ticker = aliases.get(ticker.upper(), ticker.upper())
    price_string = lookup_stock_price(ticker)
    if "not found" in price_string:
        return "Error: Ticker not found."
    clean_price = float(price_string.replace("$", ""))
    return f"${clean_price * quantity:,.2f}"

def calculate_shares_from_budget(ticker: str, budget: float):
    """
    Calculates how many shares one can buy with a specific budget.
    """
    aliases = {"GOOGLE": "GOOGL", "MICROSOFT": "MSFT", "ALKRIE": "GOOGL"}
    ticker = aliases.get(ticker.upper(), ticker.upper())
    price_string = lookup_stock_price(ticker)
    if "not found" in price_string:
        return "Error: Ticker not found."
    
    clean_price = float(price_string.replace("$", ""))
    
    # The Logic the AI was missing
    num_shares = budget / clean_price
    
    return f"You can buy {num_shares:.2f} shares of {ticker} with ${budget}."

my_tools = [
    lookup_stock_price,
    get_latest_news,
    get_company_info,          # NEW
    calculate_position_value,
    calculate_shares_from_budget
]

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
        model="gemini-2.5-flash",
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
                safe_text = response.text.replace("$", r"\$")

                # Show Response
                st.markdown(response.text)
                
                # Save to History
                st.session_state.messages.append({"role": "model", "content": response.text})
                
            except Exception as e:
                st.error(f"Agent Error: {e}")
