#!/usr/bin/env python3
"""
Interactive Backtest Results Viewer
Displays the latest backtest report
"""

from pathlib import Path

def load_latest_results():
    """Lädt die neuesten Backtest-Ergebnisse"""
    results_dir = Path(__file__).parent.parent.parent / 'results'
    reports_dir = results_dir / 'reports'
    trades_dir = results_dir / 'trades'
    
    # Finde neuesten Report
    reports = sorted(reports_dir.glob('backtest_*.txt'), reverse=True)
    if not reports:
        print("❌ Keine Backtest-Reports gefunden!")
        return None
    
    latest_report = reports[0]
    
    # Count pair files
    pair_files = sorted(trades_dir.glob('*.csv'))
    pair_files = [f for f in pair_files if f.stem != 'all_trades_chronological']
    
    return latest_report, pair_files


def main():
    """Hauptfunktion"""
    result = load_latest_results()
    if result is None:
        return
    
    latest_report, pair_files = result
    
    print("\n" + "="*80)
    print("MODEL X BACKTEST RESULTS VIEWER".center(80))
    print("="*80)
    print(f"\nLatest Report: {latest_report.name}")
    
    # Read report file and display
    with open(latest_report, 'r') as f:
        content = f.read()
    
    print(content)
    
    print("\n" + "="*80)
    print("📁 Detailed Results Available:".center(80))
    print("="*80)
    results_dir = Path(__file__).parent.parent.parent / 'results'
    print(f"\n  • Full Report:        {latest_report}")
    print(f"  • Chronological:      {results_dir / 'trades' / 'all_trades_chronological.csv'}")
    print(f"  • Individual Pairs:   {results_dir / 'trades' / '[PAIR].csv'} ({len(pair_files)} files)")
    print()


if __name__ == '__main__':
    main()
