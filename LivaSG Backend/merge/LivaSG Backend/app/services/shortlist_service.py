from typing import List, Dict, Any, Optional
from datetime import datetime
from ..domain.models import SavedLocation
from ..repositories.interfaces import ISavedLocationRepo

class ShortlistService:
    def __init__(self, saved_location_repo: ISavedLocationRepo):
        self.saved_location_repo = saved_location_repo

    def get_saved_locations(self) -> List[SavedLocation]:
        """Get all saved locations"""
        try:
            return self.saved_location_repo.get_saved_locations()
        except Exception as e:
            return []

    def save_location(self, location_data: Dict[str, Any]) -> SavedLocation:
        """Save a location to shortlist"""
        try:
            required_fields = ["postal_code", "address", "area"]
            for field in required_fields:
                if field not in location_data:
                    raise ValueError(f"Missing required field: {field}")

            location = SavedLocation(
                postal_code=location_data["postal_code"],
                address=location_data["address"],
                area=location_data["area"],
                name=location_data.get("name"),
                notes=location_data.get("notes")
            )
            self.saved_location_repo.saved_location(location)
            return location
        except Exception as e:
            raise ValueError(f"Failed to save location: {str(e)}")

    def delete_saved_location(self, postal_code: str) -> None:
        """Delete a saved location by postal code"""
        try:
            self.saved_location_repo.delete_location(postal_code)
        except Exception as e:
            raise ValueError(f"Failed to delete location: {str(e)}")

    def get_location(self, postal_code: str) -> Optional[SavedLocation]:
        """Get a specific saved location by postal code"""
        try:
            return self.saved_location_repo.get_location(postal_code)
        except Exception as e:
            raise ValueError(f"Failed to get location: {str(e)}")