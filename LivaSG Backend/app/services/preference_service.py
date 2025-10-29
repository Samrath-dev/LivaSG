from typing import List, Dict, Any, Optional
import csv
import json
import base64
import time
from datetime import datetime
from io import StringIO
from ..domain.models import UserPreference, SavedLocation, ExportData, WeightsProfile, ImportRequest
from ..repositories.interfaces import IPreferenceRepo, ISavedLocationRepo, IWeightsRepo

class PreferenceService:
    def __init__(
            self,
            preference_repo: IPreferenceRepo,
            saved_location_repo: ISavedLocationRepo,
            weights_repo: IWeightsRepo

    ):
        self.preference_repo = preference_repo
        self.saved_location_repo = saved_location_repo
        self.weights_repo = weights_repo
    def get_preference(self)-> UserPreference:
        preference = self.preference_repo.get_preference()
        if not preference:
            preference = UserPreference()
            self.preference_repo.save_preference(preference)
        return preference
    
    def update_preference_ranks(self, category_ranks: Dict[str,int])->UserPreference:
        preference=self.get_preference()
        preference.category_ranks=category_ranks
        preference.updated_at=datetime.now()
        self.preference_repo.save_preference(preference)
        return preference
    
    def get_saved_locations(self)-> List[SavedLocation]:
        return self.saved_location_repo.get_saved_locations()
    
    def saved_location(self, location_data: Dict[str, Any])-> SavedLocation:
        location=SavedLocation(
            postal_code=location_data["postal_code"],
            address=location_data["address"],
            area=location_data["area"],
            name=location_data.get("name"),
            notes=location_data.get("notes")
        )
        self.saved_location_repo.saved_location(location)
        return location
    def delete_saved_location(self, postal_code: str)-> None:
        self.saved_location_repo.delete_location(postal_code)

    def export_data(self)->ExportData:
        preference=self.get_preference()
        saved_locations=self.get_saved_locations()
        weights=self.weights_repo.get_active()
        return ExportData(
            preferences=preference,
            saved_locations=saved_locations,
            weights=weights,
            export_date=datetime.now()
        )
    
    def export_csv(self)->str:
        export_data=self.export_data()
        output=StringIO()
        writer=csv.writer(output)
        writer.writerow(["Export Type", "LivaSG Data Export"])
        writer.writerow(["Export Date", datetime.now().isoformat()])
        writer.writerow([])
        writer.writerow(["Preferences"])
        writer.writerow(["Category", "Rank"])
        for category, rank in export_data.preferences.category_ranks.items():
            writer.writerow([category,rank])
        writer.writerow([])
        writer.writerow(["Weights"])
        writer.writerow(["Category","Weight"])
        if export_data.weights:
            writer.writerow(["Affordability",export_data.weights.wAff])
            writer.writerow(["Accessibility",export_data.weights.wAcc])
            writer.writerow(["Amenities",export_data.weights.wAmen])
            writer.writerow(["Environment",export_data.weights.wEnv])
            writer.writerow(["Community",export_data.weights.wCom])
        writer.writerow([])

        writer.writerow(["Saved Locations"])
        writer.writerow(["Postal Code","Address","Area","Name","Notes"])
        for location in export_data.saved_locations:
            writer.writerow([
                location.postal_code,
                location.address,
                location.area,
                location.name or "",
                location.notes or ""
            ])
        return output.getvalue()
    
    def export_pdf(self)->str:
        export_data = self.export_data()
        pdf_content= f"""
LivaSG Export - {datetime.now()}

Preferences:
{chr(10).join([f"-{category}:{rank}" for category, rank in export_data.preferences.category_ranks.items()])}

Weights:
Affordability: {export_data.weights.wAff if export_data.weights else 0.2}
Accessibility: {export_data.weights.wAcc if export_data.weights else 0.2}
Amenities: {export_data.weights.wAmen if export_data.weights else 0.2}
Environment: {export_data.weights.wEnv if export_data.weights else 0.2}
Community: {export_data.weights.wCom if export_data.weights else 0.2}

Saved Locations ({len(export_data.saved_locations)}):
{chr(10).join([f"- {loc.name or loc.address} ({loc.postal_code}) - {loc.area}" for loc in export_data.saved_locations])}
        """
        return base64.b64encode(pdf_content.encode()).decode()
    
    def import_data(self, import_data: str, import_type: str="csv")->Dict[str, Any]:
        try:
            if import_type=="json":
                return self._import_json(import_data)
            elif import_type=="csv":
                return self._import_csv(import_data)
            elif import_type=="pdf":
                return self._import_pdf(import_data)
            else:
                return {"success": False, "message": f"Unsupported import type: {import_type}"}
        except Exception as e:
            return {"success": False, "Message": f"Import failed: {str(e)}"}
    
    def import_json(self, json_data: str)-> Dict[str, Any]:
        if json_data.startswith('data:application/json;base64,'):
            json_data=json_data.split(',',1)[1]
        try:
            decoded_data=base64.b64decode(json_data).decode('utf-8')
            data = json.loads(decoded_data)
        except:
            data = json.loads(json_data)
        self.preference_repo.delete_preference()
        for location in self.get_saved_locations():
            self.saved_location_repo.delete_location(location.postal_code)
        if 'preferences' in data:
            pref_data=data['preferences']
            preference=UserPreference(
                category_ranks=pref_data.get('category_ranks',{})
            )
            self.preference_repo.save_preference(preference)
        if 'saved_locations' in data:
            for loc_data in data['saved_locations']:
                location = SavedLocation(
                    postal_code=loc_data['postal_code'],
                    address=loc_data['address'],
                    area=loc_data['area'],
                    name=loc_data.get('name'),
                    notes=loc_data.get('notes')
                )
                self.saved_location_repo.saved_location(location)
        if 'weights' in data:
            weights_data = data['weights']
            weights = WeightsProfile(
                id=weights_data.get('id','imported'),
                label=weights_data.get('label', 'Imported Weights'),
                wAff=weights_data.get('wAff',0.2),
                wAcc=weights_data.get('wAcc',0.2),
                wAmen=weights_data.get('wAmen',0.2),
                wEnv=weights_data.get('wEnv',0.2),
                wCom=weights_data.get('wCom',0.2),
                
            )
            self.weights_repo.save(weights)
        return {"success": True, "message":"JSON data imported successfully"}
    
    def _import_csv(self, csv_data: str)-> Dict[str, Any]:
        self.preference_repo.delete_preference()
        for location in self.get_saved_locations():
            self.saved_location_repo.delete_location(location.postal_code)
        reader=csv.reader(StringIO(csv_data))
        lines=list(reader)
        current_section=None
        preferences={}
        for line in lines:
            if not line or not any(line):
                continue
            if line[0]== "Preferences":
                current_section="preferences"
                continue
            elif line[0]=="Weights":
                current_section="weights"
                continue
            elif line[0]=="Saved Locations":
                current_section="locations"
                continue
            elif line[0] in ["Export Type", "Export Date"]:
                continue
            if current_section=="preferences" and line[0] != "Category":
                if len(line)>=2:
                    preferences[line[0]]=int(line[1])
            elif current_section=="locations" and line[0] != "Postal Code":
                if len(line)>=3:
                    location_data ={
                        'postal_code': line[0],
                        'address': line[1],
                        'area': line[2],
                        'name': line[3] if len(line)> 3 and line[3] else None,
                        'notes': line[4] if len(line)>4 and line[4] else None
                    }
                    self.saved_location(location_data)
        if preferences:
            self.update_preference_ranks(preferences)
        return {"success": True, "message": "CSV data imported successfully"}
    
    def _import_pdf(self, pdf_data: str) -> Dict[str, Any]:
        try:
            decoded_data = base64.b64decode(pdf_data).decode('utf-8')
        except:
            return {"success": False, "message": "Invalid PDF data format"}
        
        lines = decoded_data.split('\n')
        self.preference_repo.delete_preference()
        for location in self.get_saved_locations():
            self.saved_location_repo.delete_location(location.postal_code)
        current_section=None
        preferences={}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "Preferences:" in line:
                current_section="preferences"
                continue
            elif "Saved Locations:" in line:
                current_section = "locations"
                continue

            if current_section=="preferences" and line.startswith("- "):
                parts = line[2:].split(": ")
                if len(parts)==2:
                    preferences[parts[0]]=int(parts[1])
            elif current_section=="locations" and line.startswith("- "):
                import re
                match = re.match(r"- (.+) \((\d+)\) - (.+)", line)
                if match:
                    name, postal_code, area=match.groups()
                    location_data={
                        'postal_code': postal_code,
                        'address': name,
                        'area': area,
                        'name': name
                    }
                    self.saved_location(location_data)
        if preferences:
            self.update_preference_ranks(preferences)
        return {"success": True, "message":"PDF data imported successfully"}