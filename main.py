from fasthtml.common import *
import random
import asyncio
from collections import deque
from datetime import datetime

# Create FastHTML app with WebSocket extension
app, rt = fast_app(exts='ws')


class AppState:
    """Global application state, keeping track of numbers and WebSocket connections"""
    def __init__(self):
        self.global_numbers = deque(maxlen=100)
        self.websockets = set()

    async def broadcast(self, number):
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = Ul(
            Li(
                Div(f"Number: {number}"),
                Div(timestamp, cls="timestamp"),
                cls="number-item"
            ),
            id="global-numbers-list",
            hx_swap_oob="beforeend"
        )

        for ws in self.websockets.copy():
            try:
                await ws(message)
            except:
                self.websockets.remove(ws)


state = AppState()


@rt("/")
def get():
    """Main page layout"""
    return Titled("Number Collection",
                  Style("""
            .numbers-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }
            .number-section {
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
            .numbers-list {
                max-height: 400px;
                overflow-y: auto;
            }
            .number-item {
                padding: 8px;
                margin: 4px 0;
                background: #f5f5f5;
                border-radius: 4px;
            }
            .controls {
                margin-bottom: 20px;
            }
            .timestamp {
                font-size: 0.8em;
                color: #666;
            }
        """),
                  Container(
                      # Input controls
                      Div(
                          Form(
                              Group(
                                  Input(
                                      type="number",
                                      id="number-input",
                                      name="number",
                                      placeholder="Enter a number",
                                      required=True
                                  ),
                                  Button("Confirm", type="submit")
                              ),
                              hx_post="/add-number",
                              hx_target="#local-numbers-list",
                              hx_swap="beforeend"
                          ),
                          Group(
                              Button(
                                  "Add Random Number",
                                  hx_post="/add-random-number",
                                  hx_target="#local-numbers-list",
                                  hx_swap="beforeend"
                              ),
                          ),
                          cls="controls"
                      ),

                      # Grid for local and global numbers
                      Div(
                          # Left side - Local numbers
                          Div(
                              H2("Local Generated Numbers"),
                              Ul(
                                  id="local-numbers-list",
                                  cls="numbers-list"
                              ),
                              cls="number-section"
                          ),

                          # Right side - Global numbers
                          Div(
                              H2("Global Numbers (All Instances)"),
                              Div(
                                  Ul(
                                      *[Li(
                                          Div(f"Number: {num}"),
                                          Div(datetime.now().strftime("%H:%M:%S"), cls="timestamp"),
                                          cls="number-item"
                                      ) for num in state.global_numbers],
                                      id="global-numbers-list",
                                      cls="numbers-list"
                                  ),
                                  hx_ext="ws",
                                  ws_connect="/ws"
                              ),
                              cls="number-section"
                          ),
                          cls="numbers-grid"
                      )
                  )
                  )


async def on_connect(send):
    """Handle new WebSocket connections"""
    state.websockets.add(send)
    message = Li(
        Div("Connected to number stream"),
        Div(datetime.now().strftime("%H:%M:%S"), cls="timestamp"),
        cls="number-item"
    )
    await send(message)


async def on_disconnect(ws):
    """Handle WebSocket disconnections"""
    if ws in state.websockets:
        state.websockets.remove(ws)


@app.ws('/ws', conn=on_connect, disconn=on_disconnect)
async def ws(msg: str, send):
    """WebSocket endpoint"""
    pass


@rt("/add-number")
async def post(number: float = None):
    """Add a number to the local and the global state by broadcasting it to all"""
    if number is None:
        return "Invalid input: Number is required"

    # Check if number is actually a float
    if not isinstance(number, (float, int)):
        return f"Invalid input: Must be a number instead got '{number}'"

    # Define bounds (adjust these as needed)
    MIN_VALUE = 0.0
    MAX_VALUE = 100.0

    # Check if number is within bounds
    if not MIN_VALUE <= number <= MAX_VALUE:
        return f"Invalid input: Number must be between {MIN_VALUE} and {MAX_VALUE}"
    # Update global state and broadcast
    state.global_numbers.appendleft(number)
    await state.broadcast(number)

    # Return only the local number update
    timestamp = datetime.now().strftime("%H:%M:%S")
    return Li(
        Div(f"Number: {number}"),
        Div(timestamp, cls="timestamp"),
        cls="number-item"
    )


@rt("/add-random-number")
async def post():
    """Add a random number to the local and the global state by broadcasting it to all"""
    random_num = random.uniform(-10000, 10000)

    # Update global state and broadcast
    state.global_numbers.appendleft(random_num)
    await state.broadcast(random_num)

    # Return only the local number update
    timestamp = datetime.now().strftime("%H:%M:%S")
    return Li(
        Div(f"Number: {random_num}"),
        Div(timestamp, cls="timestamp"),
        cls="number-item"
    )


serve()

# def validate_number(number):
#     if number is None:
#         return "Invalid input: Number is required"
#
#     # Check if number is actually a float
#     try:
#         number = float(number)
#     except (ValueError, TypeError):
#         return "Invalid input: Must be a number"
#
#     # Define bounds (adjust these as needed)
#     MIN_VALUE = 0.0
#     MAX_VALUE = 100.0
#
#     # Check if number is within bounds
#     if not MIN_VALUE <= number <= MAX_VALUE:
#         return f"Invalid input: Number must be between {MIN_VALUE} and {MAX_VALUE}"