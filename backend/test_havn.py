import unittest
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from connectors.spotify import SpotifyConnector
from connectors.takeout import TakeoutConnector
from connectors.apple_health import AppleHealthConnector
from connectors.bank_csv import BankCsvConnector
import engine
import db

class TestConnectors(unittest.TestCase):
    def setUp(self):
        self.spotify_file = "test_spotify.json"
        with open(self.spotify_file, "w") as f:
            json.dump([{
                "ts": "2023-01-01T12:00:00Z",
                "master_metadata_track_name": "Test Song",
                "master_metadata_album_artist_name": "Test Artist",
                "ms_played": 60000
            },
            {
                "ts": None,
                "master_metadata_track_name": "Bad Song"
            }], f)
            
        self.health_file = "test_health.xml"
        with open(self.health_file, "w") as f:
            f.write('''<HealthData>
                <Record type="HKQuantityTypeIdentifierStepCount" startDate="2023-01-01 12:00:00 +0000" value="500" unit="count"/>
                <Record type="Unknown" startDate="bad date"/>
            </HealthData>''')
            
        self.csv_file = "test_bank.csv"
        with open(self.csv_file, "w") as f:
            f.write("Date,Amount,Desc\n2023-01-01,$10.50,Coffee\nBadDate,bad,bad\n")

    def tearDown(self):
        os.remove(self.spotify_file)
        os.remove(self.health_file)
        os.remove(self.csv_file)

    def test_spotify_connector(self):
        conn = SpotifyConnector()
        res = conn.run(self.spotify_file)
        self.assertEqual(len(res["events"]), 1)
        self.assertEqual(res["events"][0]["description"], "Listened to Test Song by Test Artist")
        
    def test_health_connector(self):
        conn = AppleHealthConnector()
        res = conn.run(self.health_file)
        self.assertEqual(len(res["metrics"]), 1)
        self.assertEqual(res["metrics"][0]["value"], 500.0)
        
    def test_csv_connector(self):
        conn = BankCsvConnector()
        res = conn.run(self.csv_file, mapping={"date": "Date", "amount": "Amount", "description": "Desc"})
        self.assertEqual(len(res["metrics"]), 1)
        self.assertEqual(res["metrics"][0]["value"], 10.50)

class TestEngine(unittest.TestCase):
    def test_correlation(self):
        dates = pd.date_range("2023-01-01", periods=20)
        x = np.arange(20)
        y = 2 * x + np.random.normal(0, 0.1, 20)
        
        df1 = pd.DataFrame({"value": x}, index=dates)
        df2 = pd.DataFrame({"value": y}, index=dates)
        
        res = engine.analyze_correlation(df1, df2)
        self.assertGreater(res["pearson"]["r"], 0.9)
        self.assertLess(res["pearson"]["p_value"], 0.05)
        
    def test_no_correlation(self):
        dates = pd.date_range("2023-01-01", periods=20)
        np.random.seed(42)
        x = np.random.normal(0, 1, 20)
        y = np.random.normal(0, 1, 20)
        
        df1 = pd.DataFrame({"value": x}, index=dates)
        df2 = pd.DataFrame({"value": y}, index=dates)
        
        res = engine.analyze_correlation(df1, df2)
        self.assertLess(abs(res["pearson"]["r"]), 0.5)

class TestEndToEnd(unittest.TestCase):
    def test_e2e_insights(self):
        db_path = "test_havn.duckdb"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        conn = db.init_db(db_path)
        
        start_date = datetime(2023, 1, 1)
        import random
        random.seed(42)
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            is_focus = random.random() > 0.5
            
            commits = 10 if is_focus else 2
            listens = 20 if is_focus else 5
            
            for _ in range(commits):
                conn.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", (
                    f"gh_{i}_{_}", "github", current_date, "commit", "Commit", json.dumps({})
                ))
                
            for _ in range(listens):
                conn.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", (
                    f"sp_{i}_{_}", "spotify", current_date, "listen", "Focus", json.dumps({})
                ))
                
        events = conn.execute("SELECT DISTINCT source, type FROM daily_events").fetchall()
        
        candidates = [{"source": s, "name": n, "is_metric": False} for s, n in events]
        
        c1, c2 = candidates[0], candidates[1]
        
        df1 = engine.fetch_daily_series(conn, c1['source'], c1['name'], False)
        df2 = engine.fetch_daily_series(conn, c2['source'], c2['name'], False)
        
        corr = engine.analyze_correlation(df1, df2)
        self.assertGreater(corr["spearman"]["r"], 0.7)
        
        conn.close()
        os.remove(db_path)

if __name__ == "__main__":
    unittest.main()
