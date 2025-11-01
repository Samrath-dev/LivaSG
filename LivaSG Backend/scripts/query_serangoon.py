import sqlite3, os
DB='planning_cache.db'
if not os.path.exists(DB):
    print('DB not found')
    raise SystemExit(1)
conn=sqlite3.connect(DB)
cur=conn.cursor()
row=cur.execute("SELECT area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, calculated_at FROM planning_area_facilities WHERE area_name = ?",('Serangoon',)).fetchone()
print('Serangoon row:', row)
# List transit nodes inside the Serangoon polygon
row2 = cur.execute("SELECT geojson FROM planning_area_polygons WHERE area_name = ? LIMIT 1",('Serangoon',)).fetchone()
if not row2 or not row2[0]:
    print('No polygon for Serangoon in planning_area_polygons')
else:
    import json
    geojson=json.loads(row2[0])
    def point_in_polygon(lon, lat, polygon):
        num=len(polygon)
        j=num-1
        inside=False
        for i in range(num):
            lon_i, lat_i = polygon[i][0], polygon[i][1]
            lon_j, lat_j = polygon[j][0], polygon[j][1]
            if ((lat_i > lat) != (lat_j > lat)) and (lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i + 1e-12) + lon_i):
                inside = not inside
            j=i
        return inside
    def inside_geojson(geojson, lat, lon):
        if not geojson:
            return False
        t=geojson.get('type')
        if t=='MultiPolygon':
            for polygon_group in geojson.get('coordinates', []):
                for ring in polygon_group:
                    if point_in_polygon(lon, lat, ring):
                        return True
        elif t=='Polygon':
            for ring in geojson.get('coordinates', []):
                if point_in_polygon(lon, lat, ring):
                    return True
        return False
    nodes = cur.execute("SELECT id, name, type, latitude, longitude FROM transit_nodes").fetchall()
    inside_nodes = []
    for n in nodes:
        try:
            lat = float(n[3]); lon=float(n[4])
        except Exception:
            continue
        if inside_geojson(geojson, lat, lon):
            inside_nodes.append(n)
    print('Transit nodes inside Serangoon count:', len(inside_nodes))
    for r in inside_nodes[:50]:
        print(r)
conn.close()
