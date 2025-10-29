from typing import List, Dict, Any, Optional
import csv
import json
import base64
from datetime import datetime
from io import StringIO
from ..domain.models import ExportData, WeightsProfile, ImportRequest, UserPreference, SavedLocation
from ..repositories.interfaces import IPreferenceRepo, IWeightsRepo

class SettingsService:
    def __init__(
            self,
            preference_repo: IPreferenceRepo,
            weights_repo: IWeightsRepo
    ):
        self.preference_repo = preference_repo
        self.weights_repo = weights_repo

    def export_data(self, saved_locations: List[SavedLocation]) -> ExportData:
        """Export user data as JSON-serializable object"""
        try:
            preference = self._get_preference()
            
            weights = None
            try:
                weights = self.weights_repo.get_active()
            except Exception:
                pass

            export_data = ExportData(
                preferences=preference,
                saved_locations=saved_locations,
                weights=weights,
                export_date=datetime.now()
            )
            
            return export_data
        except Exception as e:
            raise ValueError(f"Failed to export data: {str(e)}")

    def export_csv(self, saved_locations: List[SavedLocation]) -> str:
        """Export user data as CSV format"""
        try:
            export_data = self.export_data(saved_locations)
            output = StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Export Type", "LivaSG Data Export"])
            writer.writerow(["Export Date", datetime.now().isoformat()])
            writer.writerow([])
            
            writer.writerow(["Preferences"])
            writer.writerow(["Category", "Rank"])
            for category, rank in export_data.preferences.category_ranks.items():
                writer.writerow([category, rank])
            writer.writerow([])
            
            writer.writerow(["Weights"])
            writer.writerow(["Category", "Weight"])
            if export_data.weights:
                writer.writerow(["Affordability", export_data.weights.wAff])
                writer.writerow(["Accessibility", export_data.weights.wAcc])
                writer.writerow(["Amenities", export_data.weights.wAmen])
                writer.writerow(["Environment", export_data.weights.wEnv])
                writer.writerow(["Community", export_data.weights.wCom])
            else:
                writer.writerow(["No weights data available"])
            writer.writerow([])
            
            writer.writerow(["Saved Locations"])
            writer.writerow(["Postal Code", "Address", "Area", "Name", "Notes", "Saved At"])
            for location in export_data.saved_locations:
                writer.writerow([
                    location.postal_code,
                    location.address,
                    location.area,
                    location.name or "",
                    location.notes or "",
                    location.saved_at.isoformat() if location.saved_at else ""
                ])
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to export CSV: {str(e)}")

    def export_pdf(self, saved_locations: List[SavedLocation]) -> str:
        """Export user data as base64 encoded PDF content"""
        try:
            export_data = self.export_data(saved_locations)
            
            pdf_content = f"""
LivaSG Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PREFERENCES:
{chr(10).join([f"- {category}: {rank}" for category, rank in export_data.preferences.category_ranks.items()])}

WEIGHTS:
Affordability: {export_data.weights.wAff if export_data.weights else 0.2}
Accessibility: {export_data.weights.wAcc if export_data.weights else 0.2}
Amenities: {export_data.weights.wAmen if export_data.weights else 0.2}
Environment: {export_data.weights.wEnv if export_data.weights else 0.2}
Community: {export_data.weights.wCom if export_data.weights else 0.2}

SAVED LOCATIONS ({len(export_data.saved_locations)}):
{chr(10).join([f"- {loc.address} ({loc.postal_code}) - {loc.area}" for loc in export_data.saved_locations])}

Export generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return base64.b64encode(pdf_content.encode('utf-8')).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to export PDF: {str(e)}")

    def import_data(self, import_data: str, import_type: str = "csv", 
                   preference_repo: IPreferenceRepo = None,
                   shortlist_service: Any = None) -> Dict[str, Any]:
        """Import user data from various formats"""
        try:
            if import_type == "json":
                return self._import_json(import_data, preference_repo, shortlist_service)
            elif import_type == "csv":
                return self._import_csv(import_data, preference_repo, shortlist_service)
            elif import_type == "pdf":
                return self._import_pdf(import_data, preference_repo, shortlist_service)
            else:
                return {"success": False, "message": f"Unsupported import type: {import_type}"}
        except Exception as e:
            return {"success": False, "message": f"Import failed: {str(e)}"}

    def _get_preference(self) -> UserPreference:
        """Get user preferences, create default if none exists"""
        try:
            preference = self.preference_repo.get_preference()
            if not preference:
                preference = UserPreference()
                self.preference_repo.save_preference(preference)
            return preference
        except Exception as e:
            return UserPreference()

    def _import_json(self, json_data: str, preference_repo: IPreferenceRepo, shortlist_service: Any) -> Dict[str, Any]:
        """Import data from JSON format"""
        try:
            if json_data.startswith('data:application/json;base64,'):
                json_data = json_data.split(',', 1)[1]
            
            try:
                decoded_data = base64.b64decode(json_data).decode('utf-8')
                data = json.loads(decoded_data)
            except:
                data = json.loads(json_data)
            
            preference_repo.delete_preference()
            
            if shortlist_service:
                for location in shortlist_service.get_saved_locations():
                    shortlist_service.delete_saved_location(location.postal_code)
            
            if 'preferences' in data:
                pref_data = data['preferences']
                preference = UserPreference(
                    category_ranks=pref_data.get('category_ranks', {})
                )
                preference_repo.save_preference(preference)
            
            if 'saved_locations' in data and shortlist_service:
                for loc_data in data['saved_locations']:
                    location_data = {
                        'postal_code': loc_data['postal_code'],
                        'address': loc_data['address'],
                        'area': loc_data['area'],
                        'name': loc_data.get('name'),
                        'notes': loc_data.get('notes')
                    }
                    shortlist_service.save_location(location_data)
            
            if 'weights' in data:
                weights_data = data['weights']
                weights = WeightsProfile(
                    id=weights_data.get('id', 'imported'),
                    label=weights_data.get('label', 'Imported Weights'),
                    wAff=weights_data.get('wAff', 0.2),
                    wAcc=weights_data.get('wAcc', 0.2),
                    wAmen=weights_data.get('wAmen', 0.2),
                    wEnv=weights_data.get('wEnv', 0.2),
                    wCom=weights_data.get('wCom', 0.2),
                )
                self.weights_repo.save(weights)
            
            return {"success": True, "message": "JSON data imported successfully"}
        except Exception as e:
            return {"success": False, "message": f"JSON import failed: {str(e)}"}

    def _import_csv(self, csv_data: str, preference_repo: IPreferenceRepo, shortlist_service: Any) -> Dict[str, Any]:
        """Import data from CSV format"""
        try:
            preference_repo.delete_preference()
            
            if shortlist_service:
                for location in shortlist_service.get_saved_locations():
                    shortlist_service.delete_saved_location(location.postal_code)
            
            reader = csv.reader(StringIO(csv_data))
            lines = list(reader)
            current_section = None
            preferences = {}
            
            for line in lines:
                if not line or not any(line):
                    continue
                
                if line[0] == "Preferences":
                    current_section = "preferences"
                    continue
                elif line[0] == "Weights":
                    current_section = "weights"
                    continue
                elif line[0] == "Saved Locations":
                    current_section = "locations"
                    continue
                elif line[0] in ["Export Type", "Export Date"]:
                    continue
                
                if current_section == "preferences" and line[0] != "Category":
                    if len(line) >= 2:
                        preferences[line[0]] = int(line[1])
                elif current_section == "locations" and line[0] != "Postal Code":
                    if len(line) >= 3 and shortlist_service:
                        location_data = {
                            'postal_code': line[0],
                            'address': line[1],
                            'area': line[2],
                            'name': line[3] if len(line) > 3 and line[3] else None,
                            'notes': line[4] if len(line) > 4 and line[4] else None
                        }
                        shortlist_service.save_location(location_data)
            
            if preferences:
                preference = UserPreference(category_ranks=preferences)
                preference_repo.save_preference(preference)
            
            return {"success": True, "message": "CSV data imported successfully"}
        except Exception as e:
            return {"success": False, "message": f"CSV import failed: {str(e)}"}

    def _import_pdf(self, pdf_data: str, preference_repo: IPreferenceRepo, shortlist_service: Any) -> Dict[str, Any]:
        """Import data from PDF format (basic text extraction)"""
        try:
            try:
                decoded_data = base64.b64decode(pdf_data).decode('utf-8')
            except:
                return {"success": False, "message": "Invalid PDF data format"}
            
            lines = decoded_data.split('\n')
            
            preference_repo.delete_preference()
            
            if shortlist_service:
                for location in shortlist_service.get_saved_locations():
                    shortlist_service.delete_saved_location(location.postal_code)
            
            current_section = None
            preferences = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if "PREFERENCES:" in line:
                    current_section = "preferences"
                    continue
                elif "SAVED LOCATIONS:" in line:
                    current_section = "locations"
                    continue
                
                if current_section == "preferences" and line.startswith("- "):
                    parts = line[2:].split(": ")
                    if len(parts) == 2:
                        preferences[parts[0]] = int(parts[1])
                elif current_section == "locations" and line.startswith("- ") and shortlist_service:
                    import re
                    match = re.match(r"- (.+) \((\d+)\) - (.+)", line)
                    if match:
                        name, postal_code, area = match.groups()
                        location_data = {
                            'postal_code': postal_code,
                            'address': name,
                            'area': area,
                            'name': name
                        }
                        shortlist_service.save_location(location_data)
            
            if preferences:
                preference = UserPreference(category_ranks=preferences)
                preference_repo.save_preference(preference)
            
            return {"success": True, "message": "PDF data imported successfully"}
        except Exception as e:
            return {"success": False, "message": f"PDF import failed: {str(e)}"}