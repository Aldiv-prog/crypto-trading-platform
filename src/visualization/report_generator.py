"""
Report generation for backtest and trading analysis.

This module creates comprehensive trading reports in multiple formats.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class ReportGenerator:
    """
    Generate comprehensive trading reports.
    
    Creates HTML, JSON, and text reports from backtest results.
    """
    
    def __init__(self, title: str = "Trading Report"):
        """
        Initialize report generator.
        
        Args:
            title: Report title
        """
        self.title = title
        self.content: Dict[str, Any] = {}
    
    def add_summary(self, metrics: Dict[str, Any]) -> None:
        """
        Add summary metrics section.
        
        Args:
            metrics: Dictionary of metrics
        """
        self.content['summary'] = metrics
    
    def add_trades(self, trades: List[Dict[str, Any]]) -> None:
        """
        Add trades section.
        
        Args:
            trades: List of trade details
        """
        self.content['trades'] = trades
    
    def add_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Add performance metrics section.
        
        Args:
            metrics: Performance metrics
        """
        self.content['performance'] = metrics
    
    def add_risk_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Add risk metrics section.
        
        Args:
            metrics: Risk metrics
        """
        self.content['risk'] = metrics
    
    def add_monthly_returns(self, returns: Dict[str, float]) -> None:
        """
        Add monthly returns section.
        
        Args:
            returns: Dictionary of monthly returns
        """
        self.content['monthly_returns'] = returns
    
    def generate_html(self, filename: str) -> None:
        """
        Generate HTML report.
        
        Args:
            filename: Output filename
        """
        html = self._create_html_report()
        
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"HTML report generated: {filename}")
    
    def generate_json(self, filename: str) -> None:
        """
        Generate JSON report.
        
        Args:
            filename: Output filename
        """
        report_data = {
            'title': self.title,
            'timestamp': datetime.now().isoformat(),
            'content': self.content,
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"JSON report generated: {filename}")
    
    def generate_text(self, filename: str) -> None:
        """
        Generate text report.
        
        Args:
            filename: Output filename
        """
        text = self._create_text_report()
        
        with open(filename, 'w') as f:
            f.write(text)
        
        print(f"Text report generated: {filename}")
    
    def _create_html_report(self) -> str:
        """Create HTML report string."""
        summary = self.content.get('summary', {})
        performance = self.content.get('performance', {})
        risk = self.content.get('risk', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.title}</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 2px solid #2196F3;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #2196F3;
                    margin-top: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #2196F3;
                    color: white;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .metric {{
                    display: inline-block;
                    width: 25%;
                    padding: 10px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2196F3;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{self.title}</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>Summary Metrics</h2>
                <div class="metrics">
        """
        
        # Add metrics
        for key, value in summary.items():
            if isinstance(value, float):
                html += f"""
                <div class="metric">
                    <div class="metric-value">{value:.2f}</div>
                    <div class="metric-label">{key}</div>
                </div>
                """
        
        html += """
                </div>
                
                <h2>Performance Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for key, value in performance.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html += """
                </table>
                
                <h2>Risk Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for key, value in risk.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_report(self) -> str:
        """Create text report string."""
        text = f"""
{'=' * 60}
{self.title}
{'=' * 60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY METRICS
{'-' * 60}
"""
        
        for key, value in self.content.get('summary', {}).items():
            text += f"{key:30s}: {value}\n"
        
        text += f"""
PERFORMANCE METRICS
{'-' * 60}
"""
        
        for key, value in self.content.get('performance', {}).items():
            text += f"{key:30s}: {value}\n"
        
        text += f"""
RISK METRICS
{'-' * 60}
"""
        
        for key, value in self.content.get('risk', {}).items():
            text += f"{key:30s}: {value}\n"
        
        text += f"\n{'=' * 60}\n"
        
        return text
