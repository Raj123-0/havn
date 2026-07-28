from abc import ABC, abstractmethod
from typing import Dict, Any, List
import uuid

class BaseConnector(ABC):
    """
    Base class for all data connectors.
    Connectors are responsible for parsing a raw file/API response
    and normalizing it into Events, Metrics, and Entities.
    """

    @abstractmethod
    def name(self) -> str:
        pass
        
    @abstractmethod
    def run(self, file_path: str = None, token: str = None, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """
        Runs the connector against a file or API.
        Returns a dictionary with keys: 'events', 'metrics', 'entities'
        Each value is a list of dictionaries matching the DB schema.
        """
        pass
        
    def _generate_id(self, *parts):
        return str(uuid.uuid5(uuid.NAMESPACE_OID, "_".join(str(p) for p in parts)))
