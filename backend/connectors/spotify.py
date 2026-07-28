import json
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseConnector

class SpotifyConnector(BaseConnector):
    def name(self) -> str:
        return "spotify"
        
    def run(self, file_path: str = None, token: str = None, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        if not file_path:
            return {"events": [], "metrics": [], "entities": []}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        parsed_events = []
        for item in data:
            ts_str = item.get("ts") or item.get("endTime")
            if not ts_str:
                continue
                
            track = item.get("master_metadata_track_name") or item.get("trackName")
            artist = item.get("master_metadata_album_artist_name") or item.get("artistName")
            ms_played = item.get("ms_played") or item.get("msPlayed")
            
            if not track or ms_played is None or ms_played < 30000:
                continue
                
            try:
                # Basic history might be "YYYY-MM-DD HH:MM" instead of isoformat
                if "T" not in ts_str:
                    timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=None)
                else:
                    timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            
            parsed_events.append({
                "id": self._generate_id("spotify", ts_str, track),
                "source": "spotify",
                "timestamp": timestamp,
                "type": "listen",
                "description": f"Listened to {track} by {artist}",
                "metadata": json.dumps({"track": track, "artist": artist, "ms_played": ms_played})
            })
            
        return {
            "events": parsed_events,
            "metrics": [],
            "entities": []
        }
