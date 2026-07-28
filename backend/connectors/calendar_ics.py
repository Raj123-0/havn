import json
from typing import Dict, Any, List
from datetime import datetime
from icalendar import Calendar
from .base import BaseConnector

class CalendarConnector(BaseConnector):
    def name(self) -> str:
        return "calendar"
        
    def run(self, file_path: str = None, token: str = None, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        if not file_path:
            return {"events": [], "metrics": [], "entities": []}
            
        parsed_events = []
        try:
            with open(file_path, 'rb') as f:
                cal = Calendar.from_ical(f.read())
        except Exception:
            return {"events": [], "metrics": [], "entities": []}
            
        for component in cal.walk():
            if component.name == "VEVENT":
                try:
                    summary = str(component.get('summary'))
                    dtstart = component.get('dtstart').dt
                    
                    if isinstance(dtstart, datetime):
                        timestamp = dtstart
                    else:
                        timestamp = datetime.combine(dtstart, datetime.min.time())
                        
                    parsed_events.append({
                        "id": self._generate_id("calendar", timestamp.isoformat(), summary),
                        "source": "calendar",
                        "timestamp": timestamp,
                        "type": "meeting",
                        "description": summary,
                        "metadata": json.dumps({"summary": summary})
                    })
                except Exception:
                    continue
                    
        return {
            "events": parsed_events,
            "metrics": [],
            "entities": []
        }
