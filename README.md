<h1>nasdaqFetcher</h1> 

- Interacts with the NASDAQ API to retrieve asset-related data (quotes, historical data, option chains, etc.).
- Retrieves real-time trade data and both raw and processed option chain data.
- Calculates implied volatility and option Greeks using pricing models (e.g., Black-Scholes-Merton).
- Provides dedicated functions to plot 2D & 3D representations of Greeks, option prices & implied volatilities over strike and time to expiry.

- Guide is available <a href="https://github.com/nndjoli/nasdaqFetcher/blob/main/Guide.ipynb">here.</a>

<h2>Requirements & Installation :</h2>

- Requirements: `requests`, `datetime`, `pandas`, `numpy`, `scipy`, `py_vollib_vectorized`, `matplotlib`, `re`.  
- Install using: `pip install nasdaqFetcher` (https://pypi.org/project/nasdaqFetcher/1.0.0/)
 
<h2>Example:</h2>

```python
import nasdaqFetcher

# Retrieve asset information (e.g., for AAPL)
Apple = nasdaqFetcher.Asset("AAPL", "stocks")
print(Apple.Informations())
# >>> {'Symbol': 'AAPL', 'Exchange': 'NASDAQ', 'Sector': 'Technology', ...}

# Get the asset's historical data as a DataFrame
historical_data = Apple.HistoricalData()
print(historical_data.head())

# Retrieve the most recent real-time trades (e.g., the last 5 trades)
RealtimeTrades = Apple.RealTime(NumberOfTrades=5)
print(RealtimeTrades)

# Retrieve the processed option chain data (for both calls and puts)
Options = Apple.Options(
    DataType="processed", 
    ExchangeCode="oprac", 
    Strategy="callput", 
    RiskFreeRate=0.04375,
)
print(OptionsChain.Data.head())
```

```python

# Create and display 2D plots of Greeks vs Strike & Time to Expiry:
Options.Plot2D(Type='call')

```
<p align="center">
  <img src="https://github.com/nndjoli/nasdaqFetcher/blob/main/Misc/Output2D.png" />
</p>

```python

# Create and display 3D plots of Greeks vs Strike & Time to Expiry:
Options.Plot3D(Type='call', ViewAngle=(15,45))

```

<p align="center">
  <img src="https://github.com/nndjoli/nasdaqFetcher/blob/main/Misc/Output3D.png" />
</p>


<h2>Note:</h2>

<ul> 
 <li>Implied Volatilities are calculated using the `py_vollib` library.</li>
 <li>Outliers are identified using Median Absolute deviation (MAD).</li>
 <li>An Implied Volatility Value is considered an outlier if:</li>

```math
\frac{X_i - \tilde{X}}{\mathrm{MAD}} > 3, \quad \text{where } \mathrm{MAD} = \mathrm{median}\left(|X_i - \tilde{X}|\right)
```
 <li> Greeks are then calculated for remaining options.</li>
</ul>

<h2>When plotting:</h2>

<ul> 
 <li>"Years Until Expiry" is converted into months and then rounded to the nearest multiple of 3.</li>
 <li>"Contract Strike" is rounded down to the nearest multiple of 10.</li> 
 <li>The data is then grouped by these two new columns, and the mean of the specified column is computed for each group.</li>
 <li><strong>Important</strong>: This is a basic visualization; therefore, the results should be interpreted with caution.</li>
</ul>
