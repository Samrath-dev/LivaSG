import requests
import json
import base64

BASE_URL = "http://localhost:8000"

def test_preferences():
    print("=== Testing Preference System ===\n")
    
    # 1. Get initial preferences
    print("1. Getting initial preferences...")
    response = requests.get(f"{BASE_URL}/preferences/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Initial preferences:", json.dumps(response.json(), indent=2))
    
    # 2. Update category ranks
    print("\n2. Updating category ranks...")
    ranks_data = {
        "Affordability": 1,
        "Accessibility": 2, 
        "Amenities": 3,
        "Environment": 4,
        "Community": 5
    }
    response = requests.put(f"{BASE_URL}/preferences/ranks", json=ranks_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Updated preferences:", json.dumps(response.json(), indent=2))
    
    # 3. Save a location
    print("\n3. Saving a location...")
    location_data = {
        "postal_code": "123456",
        "address": "123 Orchard Road",
        "area": "Orchard",
        "name": "Test Condo",
        "notes": "Great location for testing"
    }
    response = requests.post(f"{BASE_URL}/preferences/saved-locations", json=location_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Saved location:", json.dumps(response.json(), indent=2))
    
    # 4. Get saved locations
    print("\n4. Getting saved locations...")
    response = requests.get(f"{BASE_URL}/preferences/saved-locations")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Saved locations:", json.dumps(response.json(), indent=2))
    
    # 5. Test JSON export
    print("\n5. Testing JSON export...")
    response = requests.get(f"{BASE_URL}/preferences/export")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        export_data = response.json()
        print("Export keys:", list(export_data.keys()))
    
    # 6. Test CSV export
    print("\n6. Testing CSV export...")
    response = requests.get(f"{BASE_URL}/preferences/export/csv")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        csv_data = response.json()
        print("CSV filename:", csv_data.get('filename'))
        print("First few lines of CSV:")
        print(csv_data.get('csv_data', '')[:200] + "...")
    
    # 7. Test PDF export
    print("\n7. Testing PDF export...")
    response = requests.get(f"{BASE_URL}/preferences/export/pdf")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        pdf_data = response.json()
        print("PDF filename:", pdf_data.get('filename'))
        print("PDF data length:", len(pdf_data.get('pdf_data', '')))
    
    # 8. Test CSV import
    print("\n8. Testing CSV import...")
    
    # First get CSV data
    export_response = requests.get(f"{BASE_URL}/preferences/export/csv")
    if export_response.status_code == 200:
        csv_export = export_response.json()
        import_data = {
            "data": csv_export['csv_data'],
            "import_type": "csv"
        }
        response = requests.post(f"{BASE_URL}/preferences/import", json=import_data)
        print(f"Import status: {response.status_code}")
        if response.status_code == 200:
            print("Import result:", json.dumps(response.json(), indent=2))
    
    # 9. Clean up - delete test location
    print("\n9. Cleaning up test location...")
    response = requests.delete(f"{BASE_URL}/preferences/saved-locations/123456")
    print(f"Delete status: {response.status_code}")
    if response.status_code == 200:
        print("Cleanup successful:", response.json())
    
    print("\n=== Preference Testing Complete ===")

if __name__ == "__main__":
    test_preferences()