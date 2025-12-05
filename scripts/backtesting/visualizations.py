"""
Model X Backtest Visualizations
================================

Erstellt Grafiken für Backtest-Ergebnisse:
- Equity Curve
- Drawdown Chart
- R-Multiple Distribution
- Monthly Returns Heatmap
- Win/Loss Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys

# Set style
sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)


def create_equity_curve(trades_df, output_path=None):
    """
    Erstellt Equity Curve Grafik.
    
    Args:
        trades_df: DataFrame mit Trades (muss 'entry_time' und 'pnl_percent' haben)
        output_path: Pfad zum Speichern (optional)
    """
    # Sort by entry time
    trades_sorted = trades_df.sort_values('entry_time').copy()
    
    # Calculate cumulative return
    trades_sorted['cumulative_return'] = trades_sorted['pnl_percent'].cumsum()
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])
    
    # Equity Curve
    ax1.plot(trades_sorted['entry_time'], trades_sorted['cumulative_return'], 
             linewidth=2, color='#2E86AB', label='Equity Curve')
    ax1.fill_between(trades_sorted['entry_time'], 0, trades_sorted['cumulative_return'],
                      alpha=0.3, color='#2E86AB')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax1.set_title('Equity Curve (Cumulative Return %)', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Drawdown
    running_max = trades_sorted['cumulative_return'].cummax()
    drawdown = trades_sorted['cumulative_return'] - running_max
    
    ax2.fill_between(trades_sorted['entry_time'], 0, drawdown, 
                      color='red', alpha=0.3, label='Drawdown')
    ax2.plot(trades_sorted['entry_time'], drawdown, color='darkred', linewidth=1.5)
    ax2.set_title('Drawdown (%)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Drawdown (%)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Equity Curve saved: {output_path}")
    else:
        plt.show()
    
    plt.close()


def create_r_distribution(trades_df, output_path=None):
    """
    Erstellt R-Multiple Distribution Grafik.
    
    Args:
        trades_df: DataFrame mit Trades (muss 'pnl_r' haben)
        output_path: Pfad zum Speichern (optional)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Histogram
    ax1.hist(trades_df['pnl_r'], bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Breakeven')
    ax1.axvline(x=trades_df['pnl_r'].mean(), color='green', linestyle='--', 
                linewidth=2, label=f"Mean: {trades_df['pnl_r'].mean():.2f}R")
    ax1.set_title('R-Multiple Distribution', fontsize=14, fontweight='bold')
    ax1.set_xlabel('R-Multiple', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Box Plot
    ax2.boxplot(trades_df['pnl_r'], vert=True, patch_artist=True,
                boxprops=dict(facecolor='#2E86AB', alpha=0.7),
                medianprops=dict(color='red', linewidth=2),
                whiskerprops=dict(color='black', linewidth=1.5),
                capprops=dict(color='black', linewidth=1.5))
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax2.set_title('R-Multiple Box Plot', fontsize=14, fontweight='bold')
    ax2.set_ylabel('R-Multiple', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ R-Distribution saved: {output_path}")
    else:
        plt.show()
    
    plt.close()


def create_monthly_heatmap(trades_df, output_path=None):
    """
    Erstellt Monthly Returns Heatmap.
    
    Args:
        trades_df: DataFrame mit Trades (muss 'entry_time' und 'pnl_percent' haben)
        output_path: Pfad zum Speichern (optional)
    """
    # Sort by entry time
    trades_sorted = trades_df.sort_values('entry_time').copy()
    
    # Extract year and month
    trades_sorted['year'] = pd.to_datetime(trades_sorted['entry_time']).dt.year
    trades_sorted['month'] = pd.to_datetime(trades_sorted['entry_time']).dt.month
    
    # Group by year and month
    monthly_returns = trades_sorted.groupby(['year', 'month'])['pnl_percent'].sum().reset_index()
    
    # Pivot for heatmap
    heatmap_data = monthly_returns.pivot(index='year', columns='month', values='pnl_percent')
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 8))
    
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', center=0,
                cbar_kws={'label': 'Return (%)'}, linewidths=0.5, ax=ax)
    
    ax.set_title('Monthly Returns Heatmap (%)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Year', fontsize=12)
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Monthly Heatmap saved: {output_path}")
    else:
        plt.show()
    
    plt.close()


def create_win_loss_analysis(trades_df, output_path=None):
    """
    Erstellt Win/Loss Analysis Grafik.
    
    Args:
        trades_df: DataFrame mit Trades (muss 'pnl_r' und 'exit_reason' haben)
        output_path: Pfad zum Speichern (optional)
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Win Rate by Exit Reason
    exit_counts = trades_df['exit_reason'].value_counts()
    colors = {'tp': 'green', 'sl': 'red', 'manual': 'orange'}
    bar_colors = [colors.get(x, 'gray') for x in exit_counts.index]
    
    ax1.bar(exit_counts.index, exit_counts.values, color=bar_colors, alpha=0.7, edgecolor='black')
    ax1.set_title('Trades by Exit Reason', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Exit Reason', fontsize=12)
    ax1.set_ylabel('Count', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Win vs Loss Distribution
    wins = trades_df[trades_df['pnl_r'] > 0]['pnl_r']
    losses = trades_df[trades_df['pnl_r'] < 0]['pnl_r']
    
    ax2.hist([wins, losses], bins=30, label=['Wins', 'Losses'], 
             color=['green', 'red'], alpha=0.6, edgecolor='black')
    ax2.set_title('Win vs Loss Distribution', fontsize=14, fontweight='bold')
    ax2.set_xlabel('R-Multiple', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # 3. Cumulative Wins vs Losses
    trades_sorted = trades_df.sort_values('entry_time').copy()
    trades_sorted['cumulative_wins'] = (trades_sorted['pnl_r'] > 0).cumsum()
    trades_sorted['cumulative_losses'] = (trades_sorted['pnl_r'] < 0).cumsum()
    
    ax3.plot(trades_sorted['entry_time'], trades_sorted['cumulative_wins'], 
             color='green', linewidth=2, label='Cumulative Wins')
    ax3.plot(trades_sorted['entry_time'], trades_sorted['cumulative_losses'], 
             color='red', linewidth=2, label='Cumulative Losses')
    ax3.set_title('Cumulative Wins vs Losses', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Date', fontsize=12)
    ax3.set_ylabel('Count', fontsize=12)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # 4. Average R by Day of Week
    trades_sorted['day_of_week'] = pd.to_datetime(trades_sorted['entry_time']).dt.dayofweek
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    avg_r_by_day = trades_sorted.groupby('day_of_week')['pnl_r'].mean()
    
    bar_colors_day = ['green' if x > 0 else 'red' for x in avg_r_by_day.values]
    ax4.bar(range(len(avg_r_by_day)), avg_r_by_day.values, 
            color=bar_colors_day, alpha=0.7, edgecolor='black')
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax4.set_title('Average R by Day of Week', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Day', fontsize=12)
    ax4.set_ylabel('Average R', fontsize=12)
    ax4.set_xticks(range(len(day_names)))
    ax4.set_xticklabels(day_names)
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Win/Loss Analysis saved: {output_path}")
    else:
        plt.show()
    
    plt.close()


def create_all_visualizations(trades_csv_path, output_dir=None):
    """
    Erstellt alle Visualisierungen auf einmal.
    
    Args:
        trades_csv_path: Pfad zur Trades CSV
        output_dir: Output-Verzeichnis (optional, default: results/charts/)
    """
    # Load data
    trades_df = pd.read_csv(trades_csv_path)
    
    # Set output directory
    if output_dir is None:
        output_dir = Path(trades_csv_path).parent.parent / 'charts'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)
    
    # Create all charts
    create_equity_curve(trades_df, output_dir / f'equity_curve_{timestamp}.png')
    create_r_distribution(trades_df, output_dir / f'r_distribution_{timestamp}.png')
    create_monthly_heatmap(trades_df, output_dir / f'monthly_returns_{timestamp}.png')
    create_win_loss_analysis(trades_df, output_dir / f'win_loss_analysis_{timestamp}.png')
    
    print("="*80)
    print(f"✓ All visualizations saved to: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create backtest visualizations')
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='Path to trades CSV file')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output directory for charts')
    
    args = parser.parse_args()
    
    create_all_visualizations(args.input, args.output)
