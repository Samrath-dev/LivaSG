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
            print(f"DEBUG: Starting import, type: {import_type}, data length: {len(import_data)}")
            
            if import_type == "json":
                return self._import_json(import_data, rank_repo, shortlist_service)
            elif import_type == "csv":
                return self._import_csv(import_data, rank_repo, shortlist_service)
            else:
                return {"success": False, "message": f"Unsupported import type: {import_type}"}
        except Exception as e:
            print(f"DEBUG: Import failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Import failed: {str(e)}"}

    def _import_json(self, json_data: str, rank_repo: IRankRepo, shortlist_service: Any) -> Dict[str, Any]:
        try:
            print("DEBUG: Starting JSON import")
            print(f"DEBUG: Input data length: {len(json_data)}")
            print(f"DEBUG: First 100 chars: {json_data[:100]}")
            
            data = None
            
            try:
                print("DEBUG: Trying base64 decode...")
                if json_data.startswith('data:application/json;base64,'):
                    json_data = json_data.split(',', 1)[1]
                
                decoded_data = base64.b64decode(json_data).decode('utf-8')
                data = json.loads(decoded_data)
                print("DEBUG: Successfully decoded base64 JSON")
            except Exception as e1:
                print(f"DEBUG: Base64 decode failed: {e1}")
                
                try:
                    print("DEBUG: Trying raw JSON parse...")
                    data = json.loads(json_data)
                    print("DEBUG: Successfully parsed raw JSON")
                except Exception as e2:
                    print(f"DEBUG: Raw JSON parse failed: {e2}")
                    return {"success": False, "message": f"Invalid JSON data format: {e2}"}

            if not data:
                return {"success": False, "message": "No data found in import"}

            print(f"DEBUG: Parsed data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

            imported_count = 0
            messages = []

            if 'ranks' in data and data['ranks']:
                print("DEBUG: Importing ranks")
                try:
                    ranks_data = data['ranks']
                    ranks = RankProfile(
                        rAff=ranks_data.get('rAff', 3),
                        rAcc=ranks_data.get('rAcc', 3),
                        rAmen=ranks_data.get('rAmen', 3),
                        rEnv=ranks_data.get('rEnv', 3),
                        rCom=ranks_data.get('rCom', 3),
                    )
                    rank_repo.set(ranks)
                    imported_count += 1
                    messages.append("Ranks imported successfully")
                    print(f"DEBUG: Set ranks to: {ranks}")
                except Exception as e:
                    messages.append(f"Failed to import ranks: {str(e)}")

            if 'saved_locations' in data and shortlist_service:
                print("DEBUG: Importing saved locations")
                try:
                    shortlist_service.clear_all_locations() #remove if you want the import to append instead!!
                    locations_data = data['saved_locations']
                    if isinstance(locations_data, list):
                        for loc_data in locations_data:
                            try:
                                location_data = {
                                    'postal_code': loc_data['postal_code'],
                                    'address': loc_data['address'],
                                    'area': loc_data['area'],
                                    'name': loc_data.get('name'),
                                    'notes': loc_data.get('notes')
                                }
                                shortlist_service.save_location(location_data)
                                imported_count += 1
                            except Exception as e:
                                messages.append(f"Failed to import location {loc_data.get('postal_code', 'unknown')}: {str(e)}")
                        messages.append(f"Imported {len(locations_data)} saved locations")
                except Exception as e:
                    messages.append(f"Failed to import saved locations: {str(e)}")

            if 'weights' in data and data['weights']:
                print("DEBUG: Importing weights")
                try:
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
                    imported_count += 1
                    messages.append("Weights imported successfully")
                    print(f"DEBUG: Set weights to: {weights}")
                except Exception as e:
                    messages.append(f"Failed to import weights: {str(e)}")

            if imported_count > 0:
                return {
                    "success": True, 
                    "message": f"Successfully imported {imported_count} items",
                    "details": messages
                }
            else:
                return {
                    "success": False, 
                    "message": "No valid data found to import",
                    "details": messages
                }
                
        except Exception as e:
            print(f"DEBUG: JSON import failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"JSON import failed: {str(e)}"}

    def _import_csv(self, csv_data: str, rank_repo: IRankRepo, shortlist_service: Any) -> Dict[str, Any]:
        try:
            print("DEBUG: Starting CSV import")
            print(f"DEBUG: Input data length: {len(csv_data)}")
            print(f"DEBUG: First 100 chars: {csv_data[:100]}")
            
            processed_csv_data = None
            
            try:
                print("DEBUG: Trying base64 decode for CSV...")
                if csv_data.startswith('data:text/csv;base64,') or csv_data.startswith('data:application/octet-stream;base64,'):
                    csv_data = csv_data.split(',', 1)[1]
                    print("DEBUG: Removed data URL prefix")
                
                decoded_data = base64.b64decode(csv_data).decode('utf-8')
                processed_csv_data = decoded_data
                print("DEBUG: Successfully decoded base64 CSV")
            except Exception as e1:
                print(f"DEBUG: Base64 decode failed: {e1}")
                print("DEBUG: Using raw CSV data")
                processed_csv_data = csv_data

            if not processed_csv_data:
                return {"success": False, "message": "No CSV data found to import"}

            print(f"DEBUG: CSV data length after processing: {len(processed_csv_data)}")
            print(f"DEBUG: CSV preview: {processed_csv_data[:200]}")

            reader = csv.reader(StringIO(processed_csv_data))
            lines = list(reader)
            current_section = None
            ranks_data = {}
            imported_count = 0
            
            print(f"DEBUG: CSV has {len(lines)} lines")

            for line_num, line in enumerate(lines):
                if not line or not any(cell.strip() for cell in line):
                    continue
                
                print(f"DEBUG: Line {line_num}: {line}")
                
                section_header = line[0].strip().lower() if line[0] else ""
                
                if "rank" in section_header and len(line) == 1:
                    current_section = "ranks"
                    print("DEBUG: Entering Ranks section")
                    continue
                elif "weight" in section_header and len(line) == 1:
                    current_section = "weights" 
                    print("DEBUG: Entering Weights section")
                    continue
                elif "location" in section_header and len(line) == 1:
                    shortlist_service.clear_all_locations() #same thing remove if want append
                    current_section = "locations"
                    print("DEBUG: Entering Saved Locations section")
                    continue
                elif line[0] in ["Export Type", "Export Date"]:
                    continue
                elif "category" in section_header and "rank" in section_header:
                    continue
                elif "category" in section_header and "weight" in section_header:
                    continue
                elif "postal code" in section_header:
                    continue
                
                if current_section == "ranks" and len(line) >= 2:
                    category = line[0].strip().lower()
                    rank_value = line[1].strip()
                    print(f"DEBUG: Processing rank category: {category} = {rank_value}")
                    
                    try:
                        rank_int = int(rank_value)
                        if "affordability" in category:
                            ranks_data['rAff'] = rank_int
                        elif "accessibility" in category:
                            ranks_data['rAcc'] = rank_int
                        elif "amenities" in category:
                            ranks_data['rAmen'] = rank_int
                        elif "environment" in category:
                            ranks_data['rEnv'] = rank_int
                        elif "community" in category:
                            ranks_data['rCom'] = rank_int
                        print(f"DEBUG: Set {category} to {rank_int}")
                    except ValueError:
                        print(f"DEBUG: Invalid rank value: {rank_value}")
                        
                elif current_section == "locations" and len(line) >= 3 and shortlist_service:
                    print(f"DEBUG: Processing location: {line}")
                    try:
                        location_data = {
                            'postal_code': line[0].strip(),
                            'address': line[1].strip(),
                            'area': line[2].strip(),
                            'name': line[3].strip() if len(line) > 3 and line[3].strip() else None,
                            'notes': line[4].strip() if len(line) > 4 and line[4].strip() else None
                        }
                        shortlist_service.save_location(location_data)
                        imported_count += 1
                        print(f"DEBUG: Successfully imported location: {location_data['postal_code']}")
                    except Exception as e:
                        print(f"DEBUG: Failed to import location: {e}")
            
            print(f"DEBUG: Final ranks data: {ranks_data}")
            
            if ranks_data:
                try:
                    ranks = RankProfile(
                        rAff=ranks_data.get('rAff', 3),
                        rAcc=ranks_data.get('rAcc', 3),
                        rAmen=ranks_data.get('rAmen', 3),
                        rEnv=ranks_data.get('rEnv', 3),
                        rCom=ranks_data.get('rCom', 3),
                    )
                    print(f"DEBUG: Setting ranks to: {ranks}")
                    rank_repo.set(ranks)
                    imported_count += 1
                    print("DEBUG: Successfully set ranks")
                except Exception as e:
                    print(f"DEBUG: Failed to set ranks: {e}")
            else:
                print("DEBUG: No ranks data found in CSV")
            
            if imported_count > 0:
                return {
                    "success": True, 
                    "message": f"Successfully imported {imported_count} items from CSV"
                }
            else:
                return {
                    "success": False, 
                    "message": "No valid data found to import from CSV"
                }
                
        except Exception as e:
            print(f"DEBUG: CSV import error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"CSV import failed: {str(e)}"}