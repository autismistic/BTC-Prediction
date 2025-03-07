import pandas as pd
import numpy as np
from tkinter import Tk, Label, Button, Entry, StringVar, Frame, Listbox, Scrollbar, SINGLE, END, Checkbutton, IntVar
from tkinter.ttk import Treeview

# Load the data from Excel
file_path = 'BTC-Prediction.xlsx'
bitcoin_df = pd.read_excel(file_path, sheet_name='Bitcoin')
predictions_df = pd.read_excel(file_path, sheet_name='Predictions')

# Create a list of prediction names for the Listbox
prediction_names = predictions_df['Name'].unique()

def cumulative_price(r_initial, initial_price, N, r_final):
    growth_rates = [r_initial - (r_initial - r_final) * n / (N - 1) for n in range(N)]
    cumulative_growth = np.prod([1 + r for r in growth_rates])
    return initial_price * cumulative_growth

def find_r_initial(initial_price, prediction_price, N, r_final):
    tol = 1e-6
    r_initial_lower = r_final  # The initial rate must be at least as high as r_final
    r_initial_upper = 5.0  # Set an upper limit for the initial growth rate

    def f(r_initial):
        return cumulative_price(r_initial, initial_price, N, r_final) - prediction_price

    f_lower = f(r_initial_lower)
    f_upper = f(r_initial_upper)

    if f_lower * f_upper > 0:
        raise ValueError("Cannot find a suitable r_initial within the given range.")

    # Bisection method
    max_iter = 1000
    for _ in range(max_iter):
        r_initial_mid = (r_initial_lower + r_initial_upper) / 2
        f_mid = f(r_initial_mid)
        if abs(f_mid) < tol:
            return r_initial_mid
        elif f_lower * f_mid < 0:
            r_initial_upper = r_initial_mid
            f_upper = f_mid
        else:
            r_initial_lower = r_initial_mid
            f_lower = f_mid
    raise ValueError("Failed to converge to a solution for r_initial.")

def calculate_bitcoin():
    selected_prediction_value = prediction_listbox.get(prediction_listbox.curselection())
    selected_row = predictions_df[predictions_df['Name'] == selected_prediction_value].iloc[0]
    prediction_year = selected_row['Year']
    prediction_price = selected_row['Amount-Per-Bitcoin']
    
    btc_held = float(btc_held_var.get())
    annual_salary = float(annual_salary_var.get())
    use_btc_start_year = int(use_btc_var.get()) if use_btc_var.get() else None
    sell_percentage = float(sell_percentage_var.get()) / 100 if sell_percentage_var.get() else 0
    use_percentage = use_percentage_var.get() == 1
    
    initial_price = 65000  # Start with $65,000 for 2024
    years = range(2024, 2091)  # Until 2090 inclusive
    
    results = {'Year': [], 'Bitcoin Price': [], 'Percentage Increase': [], 'BTC Held': [], 'BTC Value': [], 'BTC Used': [], 'BTC Sold': []}
    summary_years = list(range(2030, 2091, 10))
    if 2090 not in summary_years:
        summary_years.append(2090)
    summary = {year: {'BTC Held': 0, 'BTC Value': 0, 'Total Money Used': 0, 'Bitcoin Price': 0, 'Average Money Used': 0, 'Money Used': 0} for year in summary_years}
    
    N = prediction_year - 2024  # Number of periods from 2025 to prediction year
    r_final = 0.15  # Final growth rate of 15%
    
    if N > 0:
        try:
            r_initial = find_r_initial(initial_price, prediction_price, N, r_final)
        except ValueError as e:
            print(str(e))
            return
    else:
        # If prediction year is 2024 or earlier
        r_initial = 0
    
    total_money_used = 0
    decade_money_used = 0
    years_used_in_decade = 0
    
    btc_price = initial_price
    for year in years:
        if year == 2024:
            growth_rate = 0
            btc_price = initial_price
        elif year >= 2025 and year <= prediction_year:
            n = year - 2025  # n ranges from 0 to N-1
            growth_rate = r_initial - (r_initial - r_final) * n / (N - 1) if N > 1 else r_final
            btc_price *= (1 + growth_rate)
        elif year > prediction_year:
            growth_rate = 0.15  # 15% growth after the prediction year
            btc_price *= (1 + growth_rate)
        else:
            growth_rate = 0  # No growth before 2024
        
        if use_btc_start_year and year >= use_btc_start_year:
            if use_percentage:
                btc_sold = btc_held * sell_percentage
                btc_sold_value = btc_sold * btc_price
            else:
                btc_needed = annual_salary / btc_price
                btc_sold = min(btc_needed, btc_held)
                btc_sold_value = btc_sold * btc_price
            
            years_used_in_decade += 1  # Increment only when BTC is used
        else:
            btc_sold = 0
            btc_sold_value = 0
        
        btc_held = max(btc_held - btc_sold, 0)
        btc_value = btc_held * btc_price
        total_money_used += btc_sold_value
        decade_money_used += btc_sold_value
        
        percentage_increase = (growth_rate * 100) if year != 2024 else "N/A"
        
        results['Year'].append(year)
        results['Bitcoin Price'].append(f"${btc_price:,.2f}")
        results['Percentage Increase'].append(f"{percentage_increase:.2f}%" if isinstance(percentage_increase, float) else percentage_increase)
        results['BTC Held'].append(round(btc_held, 8))
        results['BTC Value'].append(f"${btc_value:,.2f}")
        results['BTC Used'].append(round(btc_sold, 8))
        results['BTC Sold'].append(f"${btc_sold_value:,.2f}")
        
        if year in summary:
            summary[year]['BTC Held'] = round(btc_held, 8)
            summary[year]['BTC Value'] = f"${btc_value:,.2f}"
            summary[year]['Total Money Used'] = f"${total_money_used:,.2f}"
            summary[year]['Bitcoin Price'] = f"${btc_price:,.2f}"
            summary[year]['Money Used'] = f"${decade_money_used:,.2f}"
            average_money_used = (decade_money_used / years_used_in_decade) if years_used_in_decade > 0 else 0
            summary[year]['Average Money Used'] = f"${average_money_used:,.2f}"
            decade_money_used = 0  # Reset for the next period
            years_used_in_decade = 0  # Reset for the next period
    
    display_results(pd.DataFrame(results))
    display_summary(summary)

# Function to display results in the GUI
def display_results(results_df):
    for widget in result_frame.winfo_children():
        widget.destroy()
    
    tree = Treeview(result_frame, columns=('Year', 'Bitcoin Price', 'Percentage Increase', 'BTC Held', 'BTC Value', 'BTC Used', 'BTC Sold'), show='headings')
    tree.heading('Year', text='Year')
    tree.heading('Bitcoin Price', text='Bitcoin Price')
    tree.heading('Percentage Increase', text='Percentage Increase')
    tree.heading('BTC Held', text='BTC Held')
    tree.heading('BTC Value', text='BTC Value')
    tree.heading('BTC Used', text='BTC Used')
    tree.heading('BTC Sold', text='BTC Sold')
    
    for index, row in results_df.iterrows():
        tree.insert('', 'end', values=(int(row['Year']), row['Bitcoin Price'], row['Percentage Increase'], row['BTC Held'], row['BTC Value'], row['BTC Used'], row['BTC Sold']))
    
    tree.pack(fill='both', expand=True)

# Function to display the summary on the right
def display_summary(summary):
    for widget in summary_frame.winfo_children():
        widget.destroy()
    
    Label(summary_frame, text="Year").grid(row=0, column=0, sticky='w')
    Label(summary_frame, text="BTC Held").grid(row=0, column=1, sticky='w')
    Label(summary_frame, text="BTC Value").grid(row=0, column=2, sticky='w')
    Label(summary_frame, text="Bitcoin Price").grid(row=0, column=3, sticky='w')
    Label(summary_frame, text="Total Money Used").grid(row=0, column=4, sticky='w')
    Label(summary_frame, text="Average Money Used").grid(row=0, column=5, sticky='w')
    Label(summary_frame, text="Money Used").grid(row=0, column=6, sticky='w')
    
    for i, (year, data) in enumerate(summary.items()):
        Label(summary_frame, text=f"{year}:").grid(row=i+1, column=0, sticky='w')
        Label(summary_frame, text=f"{data['BTC Held']}").grid(row=i+1, column=1, sticky='w')
        Label(summary_frame, text=f"{data['BTC Value']}").grid(row=i+1, column=2, sticky='w')
        Label(summary_frame, text=f"{data['Bitcoin Price']}").grid(row=i+1, column=3, sticky='w')
        Label(summary_frame, text=f"{data['Total Money Used']}").grid(row=i+1, column=4, sticky='w')
        Label(summary_frame, text=f"{data['Average Money Used']}").grid(row=i+1, column=5, sticky='w')
        Label(summary_frame, text=f"{data['Money Used']}").grid(row=i+1, column=6, sticky='w')

# Set up the GUI
root = Tk()
root.title('Bitcoin Prediction Calculator')

frame = Frame(root)
frame.pack(pady=10, padx=10, fill='x')

# Create a scrollable listbox for prediction selection on the left
left_frame = Frame(frame)
left_frame.grid(row=0, column=0, padx=10, sticky='nw')

Label(left_frame, text="Select a Prediction:").grid(row=0, column=0)
scrollbar = Scrollbar(left_frame, orient="vertical")
prediction_listbox = Listbox(left_frame, selectmode=SINGLE, yscrollcommand=scrollbar.set, height=4)

for name in prediction_names:
    prediction_listbox.insert(END, name)

scrollbar.config(command=prediction_listbox.yview)
scrollbar.grid(row=1, column=1, sticky='ns')
prediction_listbox.grid(row=1, column=0)

# Input fields for BTC, Annual Salary, Use BTC, and percentage sell on the right
right_frame = Frame(frame)
right_frame.grid(row=0, column=1, padx=10, sticky='nw')

Label(right_frame, text="BTC:").grid(row=0, column=0, sticky='w')
btc_held_var = StringVar(value="1")
Entry(right_frame, textvariable=btc_held_var).grid(row=0, column=1, sticky='w')

Label(right_frame, text="Annual Salary ($):").grid(row=1, column=0, sticky='w')
annual_salary_var = StringVar(value="120000")
Entry(right_frame, textvariable=annual_salary_var).grid(row=1, column=1, sticky='w')

Label(right_frame, text="Use BTC:").grid(row=2, column=0, sticky='w')
use_btc_var = StringVar(value="")
Entry(right_frame, textvariable=use_btc_var).grid(row=2, column=1, sticky='w')

Label(right_frame, text="Sell % of BTC:").grid(row=3, column=0, sticky='w')
sell_percentage_var = StringVar(value="5")
Entry(right_frame, textvariable=sell_percentage_var).grid(row=3, column=1, sticky='w')

use_percentage_var = IntVar()
Checkbutton(right_frame, text="Use percentage instead of salary", variable=use_percentage_var).grid(row=4, column=0, columnspan=2, sticky='w')

Button(right_frame, text="Calculate", command=calculate_bitcoin).grid(row=5, columnspan=2, pady=10, sticky='w')

summary_frame = Frame(frame)
summary_frame.grid(row=0, column=2, padx=10, sticky='ne')

result_frame = Frame(root)
result_frame.pack(fill='both', expand=True, pady=20)

# Initial calculation and display
prediction_listbox.selection_set(0)
calculate_bitcoin()

root.mainloop()
