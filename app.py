import requests
import os
from datetime import datetime, timedelta
from flask import Flask, render_template

app = Flask(__name__)

# --- Configuration ---
FMP_API_KEY = 'fZWmyOpahjYV2bog9Ka2G9yrjZQCQTKx' # Your actual key
# Use the dedicated treasury endpoint base URL
TREASURY_API_URL = "https://financialmodelingprep.com/stable/treasury-rates"

# Hardcoded Benchmark High Rate
BENCHMARK_HIGH_RATE = 4.896 # As specified: 4.896% on 01/13/2025
BENCHMARK_HIGH_RATE_DATE = "Jan 13, 2025" # For display

# Conversion factor: 1 basis point = 0.01%
BASIS_POINT_CONVERSION = 100
# Savings per basis point drop (in *dollars*)
SAVINGS_PER_BP_DOLLAR = 1_000_000_000 # 1 Billion USD

# --- Comparative Stat Benchmarks (Estimates) ---
COST_PER_AIRCRAFT_CARRIER = 13_000_000_000 # Approx. Ford-class
COST_PER_HIGHWAY_MILE = 10_000_000      # Highly variable estimate
MEDIAN_HOUSEHOLD_INCOME = 75_000          # Approx. US median

# --- End Configuration ---

def get_current_rate() -> float | None:
    """Fetches the latest 10-year Treasury rate using the Treasury Rates API."""
    if not FMP_API_KEY or FMP_API_KEY == 'YOUR_FMP_API_KEY':
        print("Error: FMP API key not configured.")
        return None
    try:
        # Fetch latest data (no date parameters)
        url = f"{TREASURY_API_URL}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Expect a list, take the first (most recent) item
        if data and isinstance(data, list) and len(data) > 0:
            latest_data = data[0]
            if isinstance(latest_data, dict):
                rate = latest_data.get('year10')
                if rate is not None:
                    try:
                        return float(rate)
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert current 10y rate '{rate}' to float.")
                        return None
                else:
                    print(f"Warning: 'year10' field not found in latest Treasury data: {latest_data}")
                    return None
            else:
                print(f"Warning: Unexpected item format in Treasury API response list: {latest_data}")
                return None
        else:
            print(f"Warning: Unexpected API response format for Treasury rates: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Treasury rates from FMP API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred fetching Treasury rates: {e}")
        return None

@app.route('/')
def index():
    # Only call get_current_rate
    current_rate_api = get_current_rate()
    error_message = None
    # Initialize display variables
    one_year_high_display = f"{BENCHMARK_HIGH_RATE:.3f}"
    current_rate_display = "NaN"
    rate_difference_percent_display = "NaN"
    savings_dollars_display = "NaN" # Changed from savings_billion

    # Comparative stats - initialize
    num_carriers = "N/A"
    num_highway_miles = "N/A"
    num_households_income = "N/A"

    # Check if the current rate API call was successful and returned a float
    if isinstance(current_rate_api, float):
        current_rate_display = f"{current_rate_api:.2f}"

        # --- Calculations (using benchmark high rate) ---
        rate_difference_percent = max(0, BENCHMARK_HIGH_RATE - current_rate_api)
        basis_point_difference_for_savings_calc = rate_difference_percent * BASIS_POINT_CONVERSION # Keep for calculation, don't round yet

        # Calculate the savings in *dollars*
        # Use the unrounded basis points difference for more precision before final formatting
        savings_dollars_calc = basis_point_difference_for_savings_calc * SAVINGS_PER_BP_DOLLAR 

        # Assign calculated values for display
        rate_difference_percent_display = f"{rate_difference_percent:.2f}"
        # Format savings with commas
        savings_dollars_display = f"{savings_dollars_calc:,.0f}" # Round/format savings here

        # Calculate comparative stats if savings > 0
        if savings_dollars_calc > 0:
            num_carriers_calc = savings_dollars_calc / COST_PER_AIRCRAFT_CARRIER
            num_highway_miles_calc = savings_dollars_calc / COST_PER_HIGHWAY_MILE
            num_households_income_calc = savings_dollars_calc / MEDIAN_HOUSEHOLD_INCOME

            # Format comparative stats for display
            num_carriers = f"{num_carriers_calc:.1f}" # One decimal place
            num_highway_miles = f"{num_highway_miles_calc:,.0f}" # Commas, no decimals
            num_households_income = f"{num_households_income_calc:,.0f}" # Commas, no decimals
        else:
            # If savings are zero, keep N/A or set to 0
             num_carriers = "0.0"
             num_highway_miles = "0"
             num_households_income = "0"

    else:
        # If current rate API call failed or returned invalid data
        error_message = "Could not fetch valid current rate data from API."
        # Ensure relevant display variables remain "NaN" or "N/A"
        current_rate_display = "NaN"
        rate_difference_percent_display = "NaN"
        savings_dollars_display = "NaN"
        num_carriers = "N/A"
        num_highway_miles = "N/A"
        num_households_income = "N/A"

    return render_template(
        'index.html',
        one_year_high=one_year_high_display,
        benchmark_high_rate_date=BENCHMARK_HIGH_RATE_DATE,
        current_rate=current_rate_display,
        rate_difference_percent=rate_difference_percent_display,
        savings_dollars=savings_dollars_display, # Pass full dollar amount
        error_message=error_message,
        # Pass comparative stats
        num_carriers=num_carriers,
        num_highway_miles=num_highway_miles,
        num_households_income=num_households_income
    )

if __name__ == '__main__':
    # Check if the key looks like the placeholder
    if not FMP_API_KEY or FMP_API_KEY == 'YOUR_FMP_API_KEY':
         print("\n*** WARNING: FMP API key is not set or is the placeholder in app.py. API calls might fail. ***\n")
    app.run(debug=True) 