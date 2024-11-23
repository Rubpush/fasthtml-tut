from fasthtml.common import *
from fasthtml.svg import *
import random
import numpy as np  # Added for additional distribution functions
import matplotlib.pyplot as plt
import io
from scipy import stats

# Create FastHTML app and route decorator for URL path handling
app, rt = fast_app()

font = {'family': 'normal',
        'weight': 'bold',
        'size': 20}

plt.rc('font', **font)

def create_histogram_svg(numbers):
    # Create a new figure with specified size
    plt.figure(figsize=(8, 6))

    try:
        # Create histogram if there are numbers
        if numbers:
            plt.hist(numbers, bins=50, color='skyblue', edgecolor='black')
            plt.title('Number Distribution')
            plt.xlabel('Value')
            plt.ylabel('Count')
        else:
            # Create empty plot if no numbers
            plt.text(0.5, 0.5, 'No data yet', horizontalalignment='center', verticalalignment='center')
            plt.xlim(-1, 1)
            plt.ylim(-1, 1)

        # Save to SVG string
        f = io.StringIO()
        plt.savefig(f, format='svg', bbox_inches='tight')
        svg_data = f.getvalue()

        # Return just the SVG content without XML declaration
        svg_content = svg_data[svg_data.find('<svg'):]
        # Use hx-swap-oob to update the plot container
        return Div(NotStr(svg_content), id="plot-container", hx_swap_oob="true")

    finally:
        # Clean up matplotlib resources
        plt.close('all')
        f.close()

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

                      Group(
                          Group(
                              Label("Min Value:", Input(
                                  type="range",
                                  id="min-value",
                                  name="min",
                                  min="-100",
                                  max="100",
                                  value="0",
                                  style="width: 200px;",
                                  hx_trigger="input",
                                  hx_post="/update-display",
                                  hx_target="#min-display",
                                  hx_include="this,#max-value",  # Include max value for mean calculation
                              )),
                              Span("0", id="min-display", style="margin-left: 10px;")
                          ),
                          Group(
                              Label("Max Value:", Input(
                                  type="range",
                                  id="max-value",
                                  name="max",
                                  min="-100",
                                  max="100",
                                  value="100",
                                  style="width: 200px;",
                                  hx_trigger="input",
                                  hx_post="/update-display",
                                  hx_target="#max-display",
                                  hx_include="this,#min-value",  # Include min value for mean calculation
                              )),
                              Span("100", id="max-display", style="margin-left: 10px;")
                          ),
                          id="range-form"
                      ),

                      # Distribution selection buttons with number input for count
                      Group(
                          # Statistical parameters for distributions
                          Group(
                              Group(
                                  Label("Mean (Normal):", Input(
                                      type="number",
                                      id="mean-value",
                                      name="mean",
                                      value="0",
                                      style="width: 100px;height: 50px;",
                                      hx_trigger="load, every 100ms",  # Check for updates periodically
                                      hx_post="/update-mean-limits",
                                      hx_include="#range-form",  # Include min/max values
                                      hx_target="this"  # Update this input's attributes
                                  )),
                                  Label("Std Dev:", Input(
                                      type="number",
                                      id="std-value",
                                      name="std",
                                      min="0",
                                      value="1",
                                      style="width: 100px;height: 50px;",
                                  )),
                                  Label("Skewness:", Input(
                                      type="number",
                                      id="skew-value",
                                      name="skew",
                                      value="0",
                                      style="width: 100px;height: 50px;",
                                  )),
                                  Label("Kurtosis:", Input(
                                      type="number",
                                      id="kurt-value",
                                      name="kurt",
                                      value="3",  # Normal distribution has kurtosis of 3
                                      style="width: 100px;height: 50px;",
                                  )),
                              ),
                          # Distribution selection buttons with number input for count
                          Group(
                              Group(
                                  Label("Generated amount:", Input(
                                      type="number",
                                      id="num-values",
                                      name="count",
                                      min="1",
                                      max="1000",
                                      value="1",
                                      required=True,
                                      style="width: 100px;height: 50px;"
                                  )),
                              ),
                              Text("Generate Random Numbers:"),
                              Button(
                                  "Normal Distribution",
                                  hx_post="/add-random-number",
                                  hx_target="#numbers-list",
                                  hx_swap="beforeend",
                                  hx_vals='{"dist": "normal"}',
                                  hx_include="#range-form,[name='min'],[name='max'],[name='count'],[name='mean'],[name='std'],[name='skew'],[name='kurt']",
                              ),
                              Button(
                                  "Uniform Distribution",
                                  hx_post="/add-random-number",
                                  hx_target="#numbers-list",
                                  hx_swap="beforeend",
                                  hx_vals='{"dist": "uniform"}',
                                  hx_include="#range-form,[name='min'],[name='max'],[name='count']",
                              ),
                              Button(
                                  "Poisson Distribution",
                                  hx_post="/add-random-number",
                                  hx_target="#numbers-list",
                                  hx_swap="beforeend",
                                  hx_vals='{"dist": "poisson"}',
                                  hx_include="#range-form,[name='min'],[name='max'],[name='count']",
                              ),
                              Button(
                                  "Exponential Distribution",
                                  hx_post="/add-random-number",
                                  hx_target="#numbers-list",
                                  hx_swap="beforeend",
                                  hx_vals='{"dist": "exponential"}',
                                  hx_include="#range-form,[name='min'],[name='max'],[name='count']",
                              ),
                          ),
                        ),
                      ),

                      # Button which clears the list of stored numbers
                      Button(
                          "Clear Numbers",
                          hx_post="/clear-numbers",  # Endpoint to clear stored numbers
                          hx_target="#numbers-list",  # Target to clear the list on the client side
                          hx_swap="outerHTML"  # Replace the entire list with empty list
                      ),

                      H2("Stored Numbers:"),
                      # Show a list with stored numbers on the left and a graph on the right
                      Group(
                          Div(
                              # Create list with stored numbers, giving it an ID for HTMX targeting
                              Ul(
                                  *[Li(str(num)) for num in session.get('numbers', [])],
                                  id="numbers-list"
                              ),
                              style="flex: 1;"
                          ),
                          Div(
                              # Initial plot
                              create_histogram_svg(session['numbers']),
                              id="plot-container",
                              style="flex: 2;"
                          ),
                          style="display: flex; gap: 20px;"
                      )
                  ))


@rt("/update-display")
def post(min: float = None, max: float = None):
    responses = []

    # Update the display value for whichever slider changed
    if min is not None:
        responses.append((Span(str(round(float(min), 2)), id="min-display")))
    if max is not None:
        responses.append((Span(str(round(float(max), 2)), id="max-display")))

    # Add mean value update with the new range
    if min is not None or max is not None:
        # Get both current values from the request or use defaults
        current_min = float(min if min is not None else 0)
        current_max = float(max if max is not None else 100)
        # Calculate new mean value
        new_mean = (current_min + current_max) / 2

        # Add updated mean input to responses
        responses.append(Input(
            type="number",
            id="mean-value",
            name="mean",
            min=current_min,
            max=current_max,
            value=new_mean,
            style="width: 100px;height: 50px;",
            hx_swap_oob="true"  # Update out of band
        ))

    return responses

@rt("/add-number")
def post(session, number: float = None):
    # Return early if no valid number was provided in the form
    if number is None:
        return "Invalid input"

    # Store the new number in session and get current list
    numbers = session.get('numbers', [])
    numbers.append(number)
    session['numbers'] = numbers

    # Return both new list item and updated plot using out-of-band swap
    return Li(str(round(number, 2))), create_histogram_svg(numbers)


@rt("/add-random-number")
def post(session,
         dist: str = "uniform",
         min: float = 0,
         max: float = 100,
         count: int = 1,
         mean: float = 0,
         std: float = 1,
         skew: float = 0,
         kurt: float = 3):
    # Get existing numbers from session
    numbers = session.get('numbers', [])

    # Generate batch of random numbers using vectorized function
    new_numbers = generate_random_numbers(
        count=count,
        dist=dist,
        mean=mean,
        std=std,
        min_val=min,
        max_val=max,
        skew=skew,
        kurt=kurt
    )

    # Convert to Python list and round to 2 decimal places
    new_numbers = [round(float(x), 2) for x in new_numbers]

    # Create response elements
    responses = [Li(str(num)) for num in new_numbers]

    # Update session numbers
    numbers.extend(new_numbers)
    session['numbers'] = numbers

    # Return new list items and updated histogram
    return responses + [create_histogram_svg(session['numbers'])]


def generate_random_numbers(count, dist="uniform", mean=0, std=1, min_val=0, max_val=1,
                            skew=0, kurt=3):
    """
    Vectorized random number generation for large counts.
    """
    try:
        if dist == "normal":
            if skew == 0 and kurt == 3:
                return np.random.normal(loc=float(mean),
                                        scale=float(std),
                                        size=int(count))
            else:
                return stats.skewnorm.rvs(float(skew),
                                          loc=float(mean),
                                          scale=float(std),
                                          size=int(count))

        elif dist == "poisson":
            lambda_param = float(max_val) / 2
            return np.random.poisson(lam=lambda_param,
                                     size=int(count))

        elif dist == "exponential":
            scale = float(max_val) / 2
            return np.random.exponential(scale=scale,
                                         size=int(count))

        else:  # uniform distribution as default
            return np.random.uniform(low=float(min_val),
                                     high=float(max_val),
                                     size=int(count))
    except Exception as e:
        print(f"Error generating random numbers: {str(e)}")
        # Return uniform distribution as fallback
        return np.random.uniform(low=float(min_val),
                                 high=float(max_val),
                                 size=int(count))

@rt("/clear-numbers")
def post(session):
    # Clear the stored numbers list in session
    session['numbers'] = []

    # Return empty list and reset plot using out-of-band swap
    return Ul(id="numbers-list"), create_histogram_svg([])

# Start the FastHTML development server
serve()