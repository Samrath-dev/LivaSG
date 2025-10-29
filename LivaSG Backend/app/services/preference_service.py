from typing import Dict
from datetime import datetime
from ..domain.models import UserPreference
from ..repositories.interfaces import IPreferenceRepo

class PreferenceService:
    def __init__(self, preference_repo: IPreferenceRepo):
        self.preference_repo = preference_repo

    def get_preference(self) -> UserPreference:
        """Get user preferences, create default if none exists"""
        try:
            preference = self.preference_repo.get_preference()
            if not preference:
                preference = UserPreference()
                self.preference_repo.save_preference(preference)
            return preference
        except Exception as e:
            # Fallback to default preferences
            return UserPreference()

    def update_preference_ranks(self, category_ranks: Dict[str, int]) -> UserPreference:
        """Update category ranks in user preferences"""
        try:
            preference = self.get_preference()
            preference.category_ranks = category_ranks
            preference.updated_at = datetime.now()
            self.preference_repo.save_preference(preference)
            return preference
        except Exception as e:
            raise ValueError(f"Failed to update preference ranks: {str(e)}")