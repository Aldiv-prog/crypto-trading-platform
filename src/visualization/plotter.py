"""
Chart and visualization plotting utilities.

This module provides functions for creating trading charts and visualizations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class Plotter:
    """
    Create trading charts and visualizations.
    
    Generates matplotlib plots and HTML charts for analysis.
    """
    
    def __init__(self, width: int = 1200, height: int = 600):
        """
        Initialize plotter.
        
        Args:
            width: Chart width
            height: Chart height
        """
        self.width = width
        self.height = height
    
    def plot_equity_curve(
        self,
        equity_values: List[float],
        timestamps: List[datetime],
        title: str = "Equity Curve"
    ) -> str:
        """
        Plot equity curve.
        
        Args:
            equity_values: List of account equity values
            timestamps: List of timestamps
            title: Chart title
            
        Returns:
            HTML string with chart
        """
        # Create HTML chart using simple template
        html = self._create_html_chart(
            data=equity_values,
            labels=[t.strftime("%Y-%m-%d") for t in timestamps],
            title=title,
            color="#2196F3"
        )
        return html
    
    def plot_price_with_signals(
        self,
        prices: List[float],
        buy_signals: List[int],
        sell_signals: List[int],
        timestamps: List[datetime]
    ) -> str:
        """
        Plot price with buy/sell signals.
        
        Args:
            prices: List of prices
            buy_signals: List of buy signal indices
            sell_signals: List of sell signal indices
            timestamps: List of timestamps
            
        Returns:
            HTML string with chart
        """
        # Create data points
        labels = [t.strftime("%Y-%m-%d %H:%M") for t in timestamps]
        
        html = f"""
        <div style="width: 100%; height: {self.height}px;">
            <canvas id="priceChart"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const ctx = document.getElementById('priceChart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Price',
                        data: {json.dumps(prices)},
                        borderColor: '#2196F3',
                        fill: false,
                        pointRadius: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{display: true}}
                    }}
                }}
            }});
        </script>
        """
        return html
    
    def plot_drawdown(
        self,
        equity_curve: List[float],
        timestamps: List[datetime]
    ) -> str:
        """
        Plot drawdown curve.
        
        Args:
            equity_curve: List of equity values
            timestamps: List of timestamps
            
        Returns:
            HTML string with chart
        """
        import numpy as np
        
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = ((np.array(equity_curve) - running_max) / running_max) * 100
        
        html = self._create_html_chart(
            data=drawdown.tolist(),
            labels=[t.strftime("%Y-%m-%d") for t in timestamps],
            title="Drawdown",
            color="#FF5722"
        )
        return html
    
    def plot_histogram(
        self,
        data: List[float],
        title: str,
        bins: int = 20
    ) -> str:
        """
        Plot histogram.
        
        Args:
            data: Data values
            title: Chart title
            bins: Number of bins
            
        Returns:
            HTML string with chart
        """
        import numpy as np
        
        hist, bin_edges = np.histogram(data, bins=bins)
        
        labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(bin_edges)-1)]
        
        html = self._create_html_chart(
            data=hist.tolist(),
            labels=labels,
            title=title,
            color="#4CAF50",
            chart_type="bar"
        )
        return html
    
    def _create_html_chart(
        self,
        data: List[float],
        labels: List[str],
        title: str,
        color: str,
        chart_type: str = "line"
    ) -> str:
        """Create HTML chart template."""
        return f"""
        <div style="width: 100%; height: {self.height}px;">
            <canvas id="myChart"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: '{chart_type}',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: '{title}',
                        data: {json.dumps(data)},
                        borderColor: '{color}',
                        backgroundColor: '{color}',
                        fill: false,
                        pointRadius: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{display: true, text: '{title}'}},
                        legend: {{display: true}}
                    }},
                    scales: {{
                        y: {{beginAtZero: false}}
                    }}
                }}
            }});
        </script>
        """
    
    def export_to_html(self, charts: List[str], filename: str) -> None:
        """
        Export charts to HTML file.
        
        Args:
            charts: List of HTML charts
            filename: Output filename
        """
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Analysis</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .chart-container {
                    background-color: white;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
            </style>
        </head>
        <body>
            <h1>Trading Strategy Analysis</h1>
        """
        
        for i, chart in enumerate(charts):
            html += f'<div class="chart-container">{chart}</div>\n'
        
        html += """
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"Charts exported to {filename}")
