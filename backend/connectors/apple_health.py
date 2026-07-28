import xml.etree.ElementTree as ET
import json
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseConnector

class AppleHealthConnector(BaseConnector):
    def name(self) -> str:
        return "health"
        
    def run(self, file_path: str = None, token: str = None, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        if not file_path:
            return {"events": [], "metrics": [], "entities": []}
            
        parsed_metrics = []
        try:
            context = ET.iterparse(file_path, events=('end',))
            for event, elem in context:
                if elem.tag == 'Record':
                    type_attr = elem.get("type")
                    if type_attr in ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierHeartRate"]:
                        try:
                            start_date_str = elem.get("startDate")
                            value_str = elem.get("value")
                            unit = elem.get("unit")
                            
                            timestamp = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S %z")
                            
                            metric_name = "steps" if "StepCount" in type_attr else "heart_rate"
                            
                            parsed_metrics.append({
                                "id": self._generate_id("health", timestamp.isoformat(), metric_name),
                                "source": "apple_health",
                                "timestamp": timestamp,
                                "metric_name": metric_name,
                                "value": float(value_str),
                                "unit": unit
                            })
                        except Exception:
                            pass
                elem.clear()
        except Exception:
            pass
            
        return {
            "events": [],
            "metrics": parsed_metrics,
            "entities": []
        }
