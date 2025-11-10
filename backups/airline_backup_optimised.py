from dotenv import load_dotenv
import gradio as gr
import sqlite3
import traceback
from typing import List, Dict
from functools import wraps

# Import Azure client utilities
from backend.azure_client import get_azure_openai_client, get_azure_deployment_id


def function_tool(func):
    """Decorator to mark a function as a tool that can be called by the agent."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.is_tool = True
    return wrapper

load_dotenv(override=True)

MODEL = "gpt-4.1-mini"
AZURE_DEPLOYMENT = get_azure_deployment_id(MODEL)

# Initialize Azure OpenAI client
client = get_azure_openai_client()

instructions = """You are a helpful assistant for an Airline called FlightAI. 
Use your tools to get ticket prices and calculate discounts. Trips to London have a 10% discount on the price. 
Always be accurate. If you don't know the answer, say so."""

DB = "prices.db"
initial_ticket_prices = {"london": 799, "paris": 899, "tokyo": 1400, "sydney": 2999}


with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)")
    for city, price in initial_ticket_prices.items():
        cursor.execute(f"INSERT OR IGNORE INTO prices (city, price) VALUES ('{city}', {price})")
    conn.commit()


@function_tool
def get_ticket_price(city: str) -> str:
    """Get the price of a ticket to a given city.

    Args:
        city: The city to get the price of a ticket to
    """
    print(f"TOOL CALLED: Getting price for {city}", flush=True)
    query = f"SELECT price FROM prices WHERE city = '{city.lower()}'"
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            return f"${result[0]}" if result else "Not found"
    except Exception as e:
        return f"Error: {traceback.format_exc()}"


@function_tool
def calculate(expr: str) -> str:
    """Evaluate a numeric expression - use this for example to make calculations about prices

    Args:
        expr: The expression to evaluate
    """
    print(f"TOOL CALLED: Calculating {expr}", flush=True)
    return str(eval(expr))


async def chat(message: str, history: List[Dict[str, str]]) -> str:
    """
    Handle chat messages using Azure OpenAI.
    
    Args:
        message: The user's message
        history: List of previous messages in the conversation
        
    Returns:
        str: The assistant's response
    """
    # Format the messages for the API
    messages = [
        {"role": "system", "content": instructions},
        *[{"role": m["role"], "content": m["content"]} for m in history],
        {"role": "user", "content": message}
    ]
    
    try:
        # Call Azure OpenAI API
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=messages,
        )
        
        # Extract and return the assistant's response
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error calling Azure OpenAI: {str(e)}"
        print(error_msg)
        return "Sorry, I encountered an error processing your request. Please try again later."


if __name__ == "__main__":
    # Create the Gradio interface
    demo = gr.ChatInterface(
        fn=chat,
        title="FlightAI Assistant",
        description="Ask me about flight prices and discounts!",
        examples=["What's the price for a ticket to London?"],
        cache_examples=False,
        retry_btn=None,
        undo_btn=None,
        clear_btn="Clear",
    )
    
    # Launch the interface
    demo.launch(inbrowser=True, server_name="0.0.0.0")
