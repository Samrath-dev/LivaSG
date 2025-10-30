# app/services/settings_service.py
from typing import List, Dict, Any, Optional
import csv
import json
import base64
from datetime import datetime
from io import StringIO
from pathlib import Path
import os

from ..domain.models import ExportData, WeightsProfile, ImportRequest, RankProfile, SavedLocation
from ..repositories.interfaces import IWeightsRepo, IRankRepo

class SettingsService:
    def __init__(
            self,
            rank_repo: IRankRepo,
            weights_repo: IWeightsRepo
    ):
        self.rank_repo = rank_repo
        self.weights_repo = weights_repo
        # Create exports directory if it doesn't exist
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)

    def _save_export_to_disk(self, content: str, filename: str, export_type: str) -> str:
        """Save export to server disk and return file path"""
        try:
            file_path = self.exports_dir / filename
            
            if export_type == "json":
                file_path.write_text(content, encoding='utf-8')
            elif export_type == "csv":
                file_path.write_text(content, encoding='utf-8')
            else:
                file_path.write_text(content, encoding='utf-8')
            
            return str(file_path)
        except Exception as e:
            print(f"Warning: Failed to save export to disk: {e}")
            return ""

    def export_data(self, saved_locations: List[SavedLocation]) -> ExportData:
        """Export user data as JSON-serializable object"""
        try:
            ranks = self.rank_repo.get_active()
            
            weights = None
            try:
                weights = self.weights_repo.get_active()
            except Exception:
                pass

            export_data = ExportData(
                ranks=ranks,
                saved_locations=saved_locations,
                weights=weights,
                export_date=datetime.now()
            )
            
            return export_data
        except Exception as e:
            raise ValueError(f"Failed to export data: {str(e)}")

    def export_json(self, saved_locations: List[SavedLocation], save_to_disk: bool = True) -> Dict[str, Any]:
        try:
            export_data = self.export_data(saved_locations)
            
            # Convert to serializable dict
            data_dict = {
                "ranks": {
                    "rAff": export_data.ranks.rAff if export_data.ranks else 3,
                    "rAcc": export_data.ranks.rAcc if export_data.ranks else 3,
                    "rAmen": export_data.ranks.rAmen if export_data.ranks else 3,
                    "rEnv": export_data.ranks.rEnv if export_data.ranks else 3,
                    "rCom": export_data.ranks.rCom if export_data.ranks else 3,
                } if export_data.ranks else None,
                "saved_locations": [
                    {
                        "postal_code": loc.postal_code,
                        "address": loc.address,
                        "area": loc.area,
                        "name": loc.name,
                        "notes": loc.notes,
                        "saved_at": loc.saved_at.isoformat()
                    }
                    for loc in export_data.saved_locations
                ],
                "weights": {
                    "id": export_data.weights.id if export_data.weights else "default",
                    "name": export_data.weights.name if export_data.weights else "Default",
                    "wAff": export_data.weights.wAff if export_data.weights else 0.2,
                    "wAcc": export_data.weights.wAcc if export_data.weights else 0.2,
                    "wAmen": export_data.weights.wAmen if export_data.weights else 0.2,
                    "wEnv": export_data.weights.wEnv if export_data.weights else 0.2,
                    "wCom": export_data.weights.wCom if export_data.weights else 0.2,
                } if export_data.weights else None,
                "export_date": export_data.export_date.isoformat()
            }
            
            if save_to_disk:
                import json
                json_string = json.dumps(data_dict, indent=2)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"livasg_export_{timestamp}.json"
                saved_path = self._save_export_to_disk(json_string, filename, "json")
                if saved_path:
                    print(f"Export saved to: {saved_path}")
            
            return data_dict
        except Exception as e:
            raise ValueError(f"Failed to export JSON: {str(e)}")

    def export_csv(self, saved_locations: List[SavedLocation], save_to_disk: bool = True) -> str:
        try:
            export_data = self.export_data(saved_locations)
            output = StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Export Type", "LivaSG Data Export"])
            writer.writerow(["Export Date", datetime.now().isoformat()])
            writer.writerow([])
            
            writer.writerow(["Ranks"])
            writer.writerow(["Category", "Rank"])
            if export_data.ranks:
                writer.writerow(["Affordability", export_data.ranks.rAff])
                writer.writerow(["Accessibility", export_data.ranks.rAcc])
                writer.writerow(["Amenities", export_data.ranks.rAmen])
                writer.writerow(["Environment", export_data.ranks.rEnv])
                writer.writerow(["Community", export_data.ranks.rCom])
            else:
                writer.writerow(["No ranks data available"])
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
            
            csv_data = output.getvalue()
            
            if save_to_disk:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"livasg_export_{timestamp}.csv"
                saved_path = self._save_export_to_disk(csv_data, filename, "csv")
                if saved_path:
                    print(f"Export saved to: {saved_path}")
            
            return csv_data
        except Exception as e:
            raise ValueError(f"Failed to export CSV: {str(e)}")

    def import_data(self, import_data: str, import_type: str = "csv", 
                   rank_repo: IRankRepo = None,
                   shortlist_service: Any = None) -> Dict[str, Any]:
        try:
            if import_type == "json":
                return self._import_json(import_data, rank_repo, shortlist_service)
            elif import_type == "csv":
                return self._import_csv(import_data, rank_repo, shortlist_service)
            else:
                return {"success": False, "message": f"Unsupported import type: {import_type}"}
        except Exception as e:
            return {"success": False, "message": f"Import failed: {str(e)}"}

    def _import_json(self, json_data: str, rank_repo: IRankRepo, shortlist_service: Any) -> Dict[str, Any]:
        try:
            if json_data.startswith('data:application/json;base64,'):
                json_data = json_data.split(',', 1)[1]
            
            try:
                decoded_data = base64.b64decode(json_data).decode('utf-8')
                data = json.loads(decoded_data)
            except:
                data = json.loads(json_data)
            
            rank_repo.clear()
            
            if shortlist_service:
                for location in shortlist_service.get_saved_locations():
                    shortlist_service.delete_saved_location(location.postal_code)
            
            if 'ranks' in data and data['ranks']:
                ranks_data = data['ranks']
                ranks = RankProfile(
                    rAff=ranks_data.get('rAff', 3),
                    rAcc=ranks_data.get('rAcc', 3),
                    rAmen=ranks_data.get('rAmen', 3),
                    rEnv=ranks_data.get('rEnv', 3),
                    rCom=ranks_data.get('rCom', 3),
                )
                rank_repo.set(ranks)
            
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
            
            if 'weights' in data and data['weights']:
                weights_data = data['weights']
                weights = WeightsProfile(
                    id=weights_data.get('id', 'imported'),
                    name=weights_data.get('name', 'Imported Weights'),
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

    def _import_csv(self, csv_data: str, rank_repo: IRankRepo, shortlist_service: Any) -> Dict[str, Any]:
        try:
            rank_repo.clear()
            
            if shortlist_service:
                for location in shortlist_service.get_saved_locations():
                    shortlist_service.delete_saved_location(location.postal_code)
            
            reader = csv.reader(StringIO(csv_data))
            lines = list(reader)
            current_section = None
            ranks_data = {}
            
            for line in lines:
                if not line or not any(line):
                    continue
                
                if line[0] == "Ranks":
                    current_section = "ranks"
                    continue
                elif line[0] == "Weights":
                    current_section = "weights"
                    continue
                elif line[0] == "Saved Locations":
                    current_section = "locations"
                    continue
                elif line[0] in ["Export Type", "Export Date"]:
                    continue
                
                if current_section == "ranks" and line[0] != "Category":
                    if len(line) >= 2:
                        category = line[0].lower()
                        if "affordability" in category:
                            ranks_data['rAff'] = int(line[1])
                        elif "accessibility" in category:
                            ranks_data['rAcc'] = int(line[1])
                        elif "amenities" in category:
                            ranks_data['rAmen'] = int(line[1])
                        elif "environment" in category:
                            ranks_data['rEnv'] = int(line[1])
                        elif "community" in category:
                            ranks_data['rCom'] = int(line[1])
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
            
            if ranks_data:
                ranks = RankProfile(
                    rAff=ranks_data.get('rAff', 3),
                    rAcc=ranks_data.get('rAcc', 3),
                    rAmen=ranks_data.get('rAmen', 3),
                    rEnv=ranks_data.get('rEnv', 3),
                    rCom=ranks_data.get('rCom', 3),
                )
                rank_repo.set(ranks)
            
            return {"success": True, "message": "CSV data imported successfully"}
        except Exception as e:
            return {"success": False, "message": f"CSV import failed: {str(e)}"}