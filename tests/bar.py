import plotly.graph_objects as go
import numpy as np

x = np.random.uniform(size=10)
y = x  # Using the same values for y-axis

fig = go.Figure()
fig.add_trace(go.Bar(x=[f"{i}" for i in range(len(x))], y=y))
fig.show()