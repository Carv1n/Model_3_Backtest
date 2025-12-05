"""
Monte Carlo Equity Curve Simulation
====================================

Simuliert verschiedene Equity Curve Paths durch Trade-Randomisierung:
- Zeigt Bandbreite möglicher Equity Verläufe
- Worst-case / Best-case Szenarien
- Confidence Intervals für Equity und Drawdown
- Risiko-Analyse durch alternative Trade-Sequenzen
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime


def monte_carlo_equity_simulation(trades_df, n_simulations=1000, confidence_level=0.95, n_paths_to_plot=100):
    """
    Monte Carlo Equity Simulation durch Randomisierung der Trade-Sequenz.
    Erstellt verschiedene Equity Curve Paths.
    
    Args:
        trades_df: DataFrame mit Trades (muss 'pnl_percent' haben)
        n_simulations: Anzahl Simulationen (default: 1000)
        confidence_level: Confidence Level (default: 0.95 = 95%)
        n_paths_to_plot: Anzahl Paths in der Grafik (default: 100)
    
    Returns:
        dict mit Ergebnissen
    """
    print(f"\n{'='*80}")
    print(f"MONTE CARLO EQUITY SIMULATION")
    print(f"{'='*80}")
    print(f"Number of Simulations: {n_simulations:,}")
    print(f"Number of Trades: {len(trades_df):,}")
    print(f"Confidence Level: {confidence_level*100:.0f}%")
    print(f"Paths to Plot: {n_paths_to_plot}")
    print(f"{'='*80}\n")
    
    # Extract PnL values
    pnl_values = trades_df['pnl_percent'].values
    n_trades = len(pnl_values)
    
    # Storage for results
    all_equity_curves = []
    final_returns = []
    max_drawdowns = []
    
    # Run simulations
    for sim in range(n_simulations):
        # Randomly shuffle trade order
        shuffled_pnl = np.random.choice(pnl_values, size=n_trades, replace=False)
        
        # Calculate cumulative return (equity curve)
        equity_curve = np.cumsum(shuffled_pnl)
        all_equity_curves.append(equity_curve)
        
        # Final return
        final_return = equity_curve[-1]
        final_returns.append(final_return)
        
        # Calculate max drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = equity_curve - running_max
        max_dd = np.min(drawdown)
        max_drawdowns.append(max_dd)
        
        # Progress indicator
        if (sim + 1) % 100 == 0:
            print(f"Progress: {sim+1}/{n_simulations} simulations completed", end='\r')
    
    print(f"\nSimulations complete!\n")
    
    # Convert to arrays
    all_equity_curves = np.array(all_equity_curves)  # Shape: (n_simulations, n_trades)
    
    # Convert to arrays
    final_returns = np.array(final_returns)
    max_drawdowns = np.array(max_drawdowns)
    
    # Confidence intervals
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    # Calculate percentile bands for equity curves at each trade point
    equity_lower_band = np.percentile(all_equity_curves, lower_percentile, axis=0)
    equity_upper_band = np.percentile(all_equity_curves, upper_percentile, axis=0)
    equity_median = np.median(all_equity_curves, axis=0)
    equity_mean = np.mean(all_equity_curves, axis=0)
    
    results = {
        'n_simulations': n_simulations,
        'n_trades': n_trades,
        'confidence_level': confidence_level,
        
        # Equity curve data
        'all_equity_curves': all_equity_curves,
        'equity_median': equity_median,
        'equity_mean': equity_mean,
        'equity_lower_band': equity_lower_band,
        'equity_upper_band': equity_upper_band,
        
        # Final Return Stats
        'return_mean': np.mean(final_returns),
        'return_median': np.median(final_returns),
        'return_std': np.std(final_returns),
        'return_min': np.min(final_returns),
        'return_max': np.max(final_returns),
        'return_lower_ci': np.percentile(final_returns, lower_percentile),
        'return_upper_ci': np.percentile(final_returns, upper_percentile),
        
        # Max Drawdown Stats
        'dd_mean': np.mean(max_drawdowns),
        'dd_median': np.median(max_drawdowns),
        'dd_std': np.std(max_drawdowns),
        'dd_min': np.min(max_drawdowns),  # Best case (smallest DD)
        'dd_max': np.max(max_drawdowns),  # Worst case (largest DD)
        'dd_lower_ci': np.percentile(max_drawdowns, lower_percentile),
        'dd_upper_ci': np.percentile(max_drawdowns, upper_percentile),
        
        # Raw data for plotting
        'final_returns': final_returns,
        'max_drawdowns': max_drawdowns,
        'n_paths_to_plot': n_paths_to_plot
    }
    
    # Print results
    print(f"{'='*80}")
    print(f"MONTE CARLO RESULTS")
    print(f"{'='*80}\n")
    
    print(f"--- FINAL RETURN DISTRIBUTION ---")
    print(f"Mean:                {results['return_mean']:.2f}%")
    print(f"Median:              {results['return_median']:.2f}%")
    print(f"Std Dev:             {results['return_std']:.2f}%")
    print(f"Min (Worst Case):    {results['return_min']:.2f}%")
    print(f"Max (Best Case):     {results['return_max']:.2f}%")
    print(f"{confidence_level*100:.0f}% CI:            [{results['return_lower_ci']:.2f}%, {results['return_upper_ci']:.2f}%]")
    
    print(f"\n--- MAX DRAWDOWN DISTRIBUTION ---")
    print(f"Mean:                {results['dd_mean']:.2f}%")
    print(f"Median:              {results['dd_median']:.2f}%")
    print(f"Std Dev:             {results['dd_std']:.2f}%")
    print(f"Min (Best Case):     {results['dd_min']:.2f}%")
    print(f"Max (Worst Case):    {results['dd_max']:.2f}%")
    print(f"{confidence_level*100:.0f}% CI:            [{results['dd_lower_ci']:.2f}%, {results['dd_upper_ci']:.2f}%]")
    
    print(f"\n{'='*80}\n")
    
    return results


def plot_monte_carlo_equity(results, output_path=None):
    """
    Erstellt Visualisierung der Monte Carlo Equity Simulation.
    Zeigt verschiedene Equity Curve Paths.
    
    Args:
        results: Dict von monte_carlo_equity_simulation()
        output_path: Pfad zum Speichern (optional)
    """
    fig = plt.figure(figsize=(16, 10))
    
    # Create grid for subplots
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    ax1 = fig.add_subplot(gs[0:2, :])  # Large plot for equity curves
    ax2 = fig.add_subplot(gs[2, 0])    # Return distribution
    ax3 = fig.add_subplot(gs[2, 1])    # Drawdown distribution
    
    # 1. EQUITY CURVES WITH CONFIDENCE BANDS
    n_trades = results['n_trades']
    trade_numbers = np.arange(n_trades)
    
    # Plot sample equity curves (faded)
    n_to_plot = min(results['n_paths_to_plot'], results['n_simulations'])
    indices = np.random.choice(results['n_simulations'], n_to_plot, replace=False)
    
    for idx in indices:
        ax1.plot(trade_numbers, results['all_equity_curves'][idx], 
                color='gray', alpha=0.1, linewidth=0.5)
    
    # Plot confidence bands
    ax1.fill_between(trade_numbers, 
                     results['equity_lower_band'], 
                     results['equity_upper_band'],
                     alpha=0.3, color='blue', 
                     label=f"{results['confidence_level']*100:.0f}% Confidence Band")
    
    # Plot median and mean
    ax1.plot(trade_numbers, results['equity_median'], 
            color='red', linewidth=2, label='Median Path')
    ax1.plot(trade_numbers, results['equity_mean'], 
            color='green', linewidth=2, linestyle='--', label='Mean Path')
    
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    ax1.set_title('Monte Carlo Equity Curve Simulation', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Trade Number', fontsize=12)
    ax1.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax1.legend(fontsize=10, loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. Final Return Distribution
    ax2.hist(results['final_returns'], bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax2.axvline(results['return_mean'], color='green', linestyle='--', linewidth=2, 
                label=f"Mean: {results['return_mean']:.1f}%")
    ax2.axvline(results['return_lower_ci'], color='red', linestyle='--', linewidth=1.5,
                label=f"{results['confidence_level']*100:.0f}% CI")
    ax2.axvline(results['return_upper_ci'], color='red', linestyle='--', linewidth=1.5)
    ax2.set_title('Final Return Distribution', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Final Return (%)', fontsize=10)
    ax2.set_ylabel('Frequency', fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. Max Drawdown Distribution
    ax3.hist(results['max_drawdowns'], bins=50, color='red', alpha=0.7, edgecolor='black')
    ax3.axvline(results['dd_mean'], color='darkred', linestyle='--', linewidth=2,
                label=f"Mean: {results['dd_mean']:.1f}%")
    ax3.axvline(results['dd_lower_ci'], color='orange', linestyle='--', linewidth=1.5,
                label=f"{results['confidence_level']*100:.0f}% CI")
    ax3.axvline(results['dd_upper_ci'], color='orange', linestyle='--', linewidth=1.5)
    ax3.set_title('Max Drawdown Distribution', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Max Drawdown (%)', fontsize=10)
    ax3.set_ylabel('Frequency', fontsize=10)
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Monte Carlo Equity plot saved: {output_path}")
    else:
        plt.show()
    
    plt.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Monte Carlo Equity Simulation on backtest results')
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='Path to trades CSV file')
    parser.add_argument('-n', '--simulations', type=int, default=1000,
                       help='Number of simulations (default: 1000)')
    parser.add_argument('-p', '--paths', type=int, default=100,
                       help='Number of paths to plot (default: 100)')
    parser.add_argument('-c', '--confidence', type=float, default=0.95,
                       help='Confidence level (default: 0.95)')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output path for chart')
    
    args = parser.parse_args()
    
    # Load trades
    trades_df = pd.read_csv(args.input)
    
    # Run simulation
    results = monte_carlo_equity_simulation(trades_df, 
                                           n_simulations=args.simulations,
                                           confidence_level=args.confidence,
                                           n_paths_to_plot=args.paths)
    
    # Create plot
    if args.output:
        output_path = args.output
    else:
        output_dir = Path(args.input).parent.parent / 'charts'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f'monte_carlo_equity_{timestamp}.png'
    
    plot_monte_carlo_equity(results, output_path)
