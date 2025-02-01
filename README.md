NSDQ
---

- Interacts with the NASDAQ API to retrieve asset-related data (quotes, historical data, option chains, etc.).
- Retrieves real-time trade data and both raw and processed option chain data.
- Calculates implied volatility and option Greeks using pricing models (e.g., Black-Scholes-Merton).
- Provides a dedicated class to generate and plot the implied volatility surface using spline smoothing.  

- Guide is available <a href="https://github.com/ndjoli-nathan/NSDQ/blob/main/Guide.ipynb">here.</a>

---
 
Requirements: `requests`, `datetime`, `pandas`, `numpy`, `scipy`, `py_vollib_vectorized`, `matplotlib`, `re`.  

  
Install using: `pip install NSDQ`

---
 
Example:

```python
from MyPackages import NSDQ

# Retrieve asset information (e.g., for AAPL)
Apple = NSDQ.Asset("AAPL", "stocks")
print(Apple.Informations())
# >>> {'Symbol': 'AAPL', 'Exchange': 'NASDAQ', 'Sector': 'Technology', ...}

# Get the asset's historical data as a DataFrame
historical_data = Apple.HistoricalData()
print(historical_data.head())

# Retrieve the most recent real-time trades (e.g., the last 5 trades)
RealtimeTrades = Apple.RealTime(NumberOfTrades=5)
print(RealtimeTrades)

# Retrieve the processed option chain data (for both calls and puts)
OptionsChain = Apple.Options(
    DataType="processed", 
    ExchangeCode="oprac", 
    Strategy="callput", 
    RiskFreeRate=0.04375
)
print(OptionsChain.head())

# Create and display the implied volatility surface for call options
IVS = Apple.ImpliedVolatilitySurface("call", RiskFreeRate=0.04375)
IVS.Plot(
    SmoothingFactor=1,
    Granularity=256,
    FigSize=(12, 12),
    CMap="viridis",
    EdgeColor="none",
    Alpha=0.9,
    ViewAngle=(15, 315),
    BoxAspect=(36, 36, 18),
    ShowScatter=True
)
```
<p align="center">
  <img src="https://github.com/ndjoli-nathan/NSDQ/blob/main/GIF.gif" alt="GIF" />
</p>
