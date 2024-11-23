from fasthtml.common import *
import random

# Create FastHTML app and route decorator for URL path handling
app, rt = fast_app()


@rt("/")
def get(session):
    # Initialize empty numbers list in session if not present to ensure valid state
    if 'numbers' not in session:
        session['numbers'] = []

    return Titled("Number Collection",  # Page title for browser tab and main heading
                  Container(
                      Form(
                          Group(
                              Input(
                                  type="number",
                                  id="number-input",
                                  name="number",
                                  placeholder="Enter a number",
                                  required=True  # Prevents form submission without a value
                              ),
                              Button("Confirm", type="submit")
                          ),
                          hx_post="/add-number",  # HTMX will POST to this endpoint on form submit
                          hx_target="#numbers-list",  # Target element that will receive the response
                          hx_swap="beforeend"  # New items will be appended to the end of target
                      ),

                      # Two buttons on a single line
                      Group(
                          # Button that generates and adds random numbers to the list
                          Button(
                              "Add Random Number",
                              hx_post="/add-random-number",  # Different endpoint but same HTMX pattern as form
                              hx_target="#numbers-list",
                              hx_swap="beforeend"
                          ),
                          # Button which clears the list of stored numbers
                          Button(
                              "Clear Numbers",
                              hx_post="/clear-numbers",  # Endpoint to clear stored numbers
                              hx_target="#numbers-list",  # Target to clear the list on the client side
                              hx_swap="outerHTML"  # Replace the entire list with empty list
                          ),
                      ),

                      H2("Stored Numbers:"),
                      # Show a list with stored numbers on the left and a graph on the right
                      Group(

                      Div(
                          # Create list with stored numbers, giving it an ID for HTMX targeting
                          Ul(
                              *[Li(str(num)) for num in session.get('numbers', [])],
                              id="numbers-list"
                          )
                      ),
                    Div(
                        # Placeholder for a graph showing the distribution of stored numbers
                        "Graph placeholder",
                        style="border: 1px solid black; height: 200px; width: 200px; margin-left: 10px;"
                    ),

                  )
                )
                )


@rt("/add-number")
def post(session, number: float = None):
    # Return early if no valid number was provided in the form
    if number is None:
        return "Invalid input"

    # Store the new number in session and get current list
    numbers = session.get('numbers', [])
    numbers.append(number)
    session['numbers'] = numbers

    # Return single new list item for HTMX to append to existing list
    return Li(str(number))


@rt("/add-random-number")
def post(session):
    # Generate random number between -10000-10000 and add to session storage
    random_num = random.uniform(-10000, 10000)
    numbers = session.get('numbers', [])
    numbers.append(random_num)
    session['numbers'] = numbers

    # Return just the new random number as a list item for HTMX append
    return Li(str(random_num))


@rt("/clear-numbers")
def post(session):
    # Clear the stored numbers list in session
    session['numbers'] = []

    # Return a new empty list instead of empty string to maintain DOM structure
    return Ul(id="numbers-list")


# Start the FastHTML development server
serve()