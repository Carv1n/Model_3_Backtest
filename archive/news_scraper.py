#!/usr/bin/env python3
"""
Forex Factory FULL SCRAPER 2007-2025
- Scrapt RAW Daten (Berlin Zeit, wie von Forex Factory geliefert)
- KEINE Timezone-Korrektur hier (erfolgt in organize_data.py)
- Checkpoint-System: Skippt abgeschlossene Wochen
- Resume-Funktion: Erweitert bestehende CSV
- CHECKPOINTS BLEIBEN ERHALTEN für zukünftige Updates!
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
import json

# PFADE - Dynamisch relativ zum Script
NEWS_DIR = Path(__file__).parent.parent.parent / "News"
RAW_DIR = NEWS_DIR / "01_Raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_FILE = RAW_DIR / "scraping_checkpoints.json"
OUTPUT_FILE = RAW_DIR / "forex_calendar_raw_2007_2025.csv"

# PARAMETER
START_DATE = datetime(2007, 1, 1)  # Forex Factory älteste Daten
END_DATE = datetime(2025, 12, 31)   # Bis Ende 2025
RATE_LIMIT = 1.2  # Sekunden zwischen Wochen


def setup_driver(headless=True):
    """Selenium Driver Setup"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def load_checkpoints():
    """Lädt abgeschlossene Wochen aus Checkpoint-File"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)
            completed = [datetime.strptime(d, '%Y-%m-%d') for d in data['completed_weeks']]
            return set(completed)
    return set()


def save_checkpoint(completed_weeks):
    """Speichert abgeschlossene Wochen"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({
            'completed_weeks': [d.strftime('%Y-%m-%d') for d in sorted(completed_weeks)],
            'last_updated': datetime.now().isoformat(),
            'total_weeks': len(completed_weeks)
        }, f, indent=2)


def load_existing_data():
    """Lädt bestehende CSV falls vorhanden"""
    if OUTPUT_FILE.exists():
        df = pd.read_csv(OUTPUT_FILE)
        print(f"   ✅ Bestehende CSV gefunden: {len(df):,} Events")
        return df
    return pd.DataFrame()


def append_to_csv(new_data):
    """Erweitert bestehende CSV oder erstellt neue"""
    new_df = pd.DataFrame(new_data)
    
    if OUTPUT_FILE.exists():
        # Erweitere bestehende CSV
        existing_df = pd.read_csv(OUTPUT_FILE)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Entferne Duplikate
        combined_df = combined_df.drop_duplicates(
            subset=['DateTime', 'Currency', 'Event'], 
            keep='first'
        )
        
        combined_df.to_csv(OUTPUT_FILE, index=False)
        print(f"   💾 CSV erweitert: {len(existing_df):,} → {len(combined_df):,} Events")
    else:
        # Erstelle neue CSV
        new_df.to_csv(OUTPUT_FILE, index=False)
        print(f"   💾 CSV erstellt: {len(new_df):,} Events")


def scrape_calendar_week(driver, week_start):
    """
    Scrapt eine GANZE WOCHE
    Speichert RAW Daten (Berlin Zeit, wie von Forex Factory geliefert)
    """
    week_str = week_start.strftime("%b%d.%Y").lower()
    url = f"https://www.forexfactory.com/calendar?week={week_str}"
    
    try:
        driver.get(url)
        time.sleep(1.5)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "calendar__row"))
        )
        
        rows = driver.find_elements(By.CLASS_NAME, "calendar__row")
        
        if len(rows) == 0:
            return []
        
        week_events = []
        current_time = None
        current_date = week_start
        
        for row in rows:
            try:
                # DATUM
                date_cells = row.find_elements(By.CLASS_NAME, "calendar__date")
                if date_cells:
                    date_text = date_cells[0].text.strip()
                    if date_text:
                        try:
                            parts = date_text.split()
                            if len(parts) >= 3:
                                day_num = int(parts[-1])
                                month_map = {
                                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                                    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                }
                                month_name = parts[1].lower()[:3]
                                month_num = month_map.get(month_name, week_start.month)
                                
                                year = week_start.year
                                if month_num == 12 and week_start.month == 1:
                                    year -= 1
                                elif month_num == 1 and week_start.month == 12:
                                    year += 1
                                
                                current_date = datetime(year, month_num, day_num)
                        except:
                            pass
                
                # ZEIT
                time_cells = row.find_elements(By.CLASS_NAME, "calendar__time")
                if time_cells and time_cells[0].text.strip():
                    time_text = time_cells[0].text.strip()
                    if time_text:
                        current_time = time_text
                
                # CURRENCY
                curr_cells = row.find_elements(By.CLASS_NAME, "calendar__currency")
                if not curr_cells:
                    continue
                currency = curr_cells[0].text.strip()
                if not currency:
                    continue
                
                # IMPACT
                impact = "Unknown"
                impact_cells = row.find_elements(By.CLASS_NAME, "calendar__impact")
                if impact_cells:
                    impact_html = impact_cells[0].get_attribute('innerHTML')
                    if 'icon--ff-impact-red' in impact_html:
                        impact = "High Impact Expected"
                    elif 'icon--ff-impact-ora' in impact_html:
                        impact = "Medium Impact Expected"
                    elif 'icon--ff-impact-yel' in impact_html:
                        impact = "Low Impact Expected"
                
                # EVENT
                event_cells = row.find_elements(By.CLASS_NAME, "calendar__event")
                if not event_cells:
                    continue
                event_name = event_cells[0].text.strip()
                if not event_name:
                    continue
                
                # ACTUAL
                actual = ""
                actual_cells = row.find_elements(By.CLASS_NAME, "calendar__actual")
                if actual_cells:
                    actual = actual_cells[0].text.strip()
                
                # FORECAST
                forecast = ""
                forecast_cells = row.find_elements(By.CLASS_NAME, "calendar__forecast")
                if forecast_cells:
                    forecast = forecast_cells[0].text.strip()
                
                # PREVIOUS
                previous = ""
                previous_cells = row.find_elements(By.CLASS_NAME, "calendar__previous")
                if previous_cells:
                    previous = previous_cells[0].text.strip()
                
                # DateTime (RAW - Berlin Zeit!)
                # KEINE Korrektur hier - erfolgt in organize_data.py
                if current_time and current_time.lower() not in ['all day', 'tentative']:
                    try:
                        time_clean = current_time.replace(' ', '').lower()
                        time_obj = datetime.strptime(time_clean, '%I:%M%p')
                        dt = datetime.combine(current_date, time_obj.time())
                        dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                    except:
                        dt_str = current_date.strftime('%Y-%m-%dT00:00:00+00:00')
                else:
                    dt_str = current_date.strftime('%Y-%m-%dT00:00:00+00:00')
                
                event_data = {
                    'DateTime': dt_str,
                    'Currency': currency,
                    'Impact': impact,
                    'Event': event_name,
                    'Actual': actual if actual else None,
                    'Forecast': forecast if forecast else None,
                    'Previous': previous if previous else None,
                    'Detail': ''
                }
                
                week_events.append(event_data)
                
            except:
                continue
        
        return week_events
        
    except:
        return []


def main():
    print("=" * 70)
    print("FOREX FACTORY FULL SCRAPER 2007-2025")
    print("=" * 70)
    
    print("\n⚠️  WICHTIG:")
    print("   Dieser Scraper speichert RAW Daten (Berlin Zeit)")
    print("   UTC-Korrektur erfolgt in organize_data.py")
    
    # Lade Checkpoints
    completed_weeks = load_checkpoints()
    
    # Lade bestehende Daten
    existing_df = load_existing_data()
    
    if len(completed_weeks) > 0:
        print(f"\n🔄 RESUME-MODUS")
        print(f"   ✅ {len(completed_weeks)} Wochen bereits abgeschlossen")
        print(f"   📊 {len(existing_df):,} Events bereits vorhanden")
        
        last_completed = max(completed_weeks)
        next_week = last_completed + timedelta(weeks=1)
        
        resume = input(f"\n   Fortsetzen ab {next_week.date()}? (j/n): ").strip().lower()
        if resume == 'j':
            start_week = next_week
        else:
            start_week = START_DATE
            completed_weeks = set()
            if OUTPUT_FILE.exists():
                OUTPUT_FILE.unlink()
            print("   🗑️  Alte Daten gelöscht, starte von vorne")
    else:
        start_week = START_DATE
    
    # Berechne Wochen
    all_weeks = []
    current = start_week
    while current <= END_DATE:
        if current not in completed_weeks:
            all_weeks.append(current)
        current += timedelta(weeks=1)
    
    total_weeks = len(all_weeks)
    estimated_hours = (total_weeks * RATE_LIMIT) / 3600
    
    print(f"\n📊 SCRAPING PLAN:")
    print(f"├─ Start:        {start_week.date()}")
    print(f"├─ Ende:         {END_DATE.date()}")
    print(f"├─ Zu scrapen:   {total_weeks:,} Wochen")
    print(f"├─ Übersprungen: {len(completed_weeks):,} Wochen")
    print(f"├─ Rate:         {RATE_LIMIT}s pro Woche")
    print(f"└─ Geschätzt:    ~{estimated_hours:.1f} Stunden")
    
    print(f"\n💾 OUTPUT:")
    print(f"├─ CSV:          {OUTPUT_FILE.name} (RAW - Berlin Zeit)")
    print(f"└─ Checkpoints:  {CHECKPOINT_FILE.name}")
    
    print(f"\n⚠️  Daten werden als RAW gespeichert (Berlin Zeit)")
    print(f"   UTC-Korrektur erfolgt später in organize_data.py")
    
    confirm = input(f"\n✅ Starten? (j/n): ").strip().lower()
    if confirm != 'j':
        return
    
    # SETUP
    print(f"\n[1/3] Starte Browser...")
    use_headless = input("   Headless? (j=schneller): ").strip().lower() == 'j'
    driver = setup_driver(headless=use_headless)
    print("✅ Browser bereit")
    
    # SCRAPE
    print(f"\n[2/3] Scrape {total_weeks:,} Wochen...")
    print("=" * 70)
    
    buffer = []
    buffer_size = 0
    weeks_in_buffer = []  # Track welche Wochen im Buffer sind
    save_interval = 5  # Speichere alle 5 Wochen
    start_time = time.time()

    for i, week_start in enumerate(all_weeks, 1):
        # Scrape
        week_data = scrape_calendar_week(driver, week_start)
        buffer.extend(week_data)
        buffer_size += len(week_data)
        weeks_in_buffer.append(week_start)  # Track diese Woche

        # Progress (alle 10 Wochen)
        if i % 10 == 0 or i == total_weeks:
            elapsed = time.time() - start_time
            weeks_remaining = total_weeks - i
            estimated_remaining = (weeks_remaining * RATE_LIMIT) / 3600

            print(f"\n📊 Woche {i}/{total_weeks} ({week_start.date()})")
            print(f"   ├─ Buffer:      {buffer_size:,} Events ({len(weeks_in_buffer)} Wochen)")
            print(f"   ├─ Elapsed:     {elapsed/3600:.1f}h")
            print(f"   └─ Remaining:   ~{estimated_remaining:.1f}h")

        # Speichere alle 5 Wochen ODER am Ende
        if i % save_interval == 0 or i == total_weeks:
            if len(buffer) > 0:
                append_to_csv(buffer)
                # Checkpoint NUR für KOMPLETT abgeschlossene Wochen
                # (alle außer der letzten im Buffer - die könnte unvollständig sein)
                weeks_to_checkpoint = weeks_in_buffer[:-1] if i != total_weeks else weeks_in_buffer
                for week in weeks_to_checkpoint:
                    completed_weeks.add(week)
                save_checkpoint(completed_weeks)

                buffer = []
                buffer_size = 0
                weeks_in_buffer = []  # Reset

        time.sleep(RATE_LIMIT)
    
    driver.quit()
    print("\n✅ Browser geschlossen")
    
    # FINAL STATS
    print("\n" + "=" * 70)
    print("SCRAPING ABGESCHLOSSEN")
    print("=" * 70)
    
    total_time = time.time() - start_time
    final_df = pd.read_csv(OUTPUT_FILE)
    
    print(f"\n📊 FINAL STATISTIKEN:")
    print(f"├─ Total Events:      {len(final_df):,}")
    print(f"├─ Zeitraum:          {final_df['DateTime'].min()[:10]} - {final_df['DateTime'].max()[:10]}")
    print(f"├─ Currencies:        {final_df['Currency'].nunique()}")
    print(f"├─ Wochen gescrapt:   {len(completed_weeks):,}")
    print(f"└─ Gesamtdauer:       {total_time/3600:.1f} Stunden")
    
    print(f"\n📂 OUTPUT: {OUTPUT_FILE}")
    print(f"\n⚠️  WICHTIG: Daten sind in Berlin Zeit!")
    
    # CHECKPOINTS BLEIBEN ERHALTEN!
    print(f"\n✅ Checkpoints gespeichert in: {CHECKPOINT_FILE}")
    print(f"   └─ {len(completed_weeks):,} Wochen dokumentiert")
    print(f"\n💡 Für zukünftige Updates einfach Script erneut starten!")
    print(f"   Das Script wird automatisch nur neue Wochen scrapen.")
    
    print(f"\n✅ FERTIG!")
    print(f"\n💡 NÄCHSTER SCHRITT:")
    print(f"   python organize_data.py  # Macht UTC-Korrektur & organisiert Daten")


if __name__ == "__main__":
    main()