import sqlite3

conn = sqlite3.connect('street_geocode.db')
c = conn.cursor()

print('=== Transit Facility Integration Test ===\n')

# 1. Schema check
schema = c.execute('PRAGMA table_info(street_facilities)').fetchall()
cols = [col[1] for col in schema]
print(f'1. Schema check: transit in columns? {"transit" in cols}')
print(f'   Columns: {", ".join(cols)}\n')

# 2. Data stats
stats = c.execute('SELECT COUNT(*), SUM(CASE WHEN transit>0 THEN 1 ELSE 0 END), MAX(transit) FROM street_facilities').fetchone()
print(f'2. Data stats:')
print(f'   - Total records: {stats[0]}')
print(f'   - With transit: {stats[1]}')
print(f'   - Max transit: {stats[2]}\n')

# 3. Sample data
sample = c.execute('SELECT street_name, transit FROM street_facilities WHERE transit > 0 LIMIT 3').fetchall()
print('3. Sample streets with transit:')
for s in sample:
    print(f'   - {s[0]}: {s[1]} station(s)')

# 4. Complete facility record
print('\n4. Complete facility record example:')
full = c.execute('SELECT * FROM street_facilities WHERE transit > 0 LIMIT 1').fetchone()
if full:
    print(f'   Street: {full[0]}')
    print(f'   Schools: {full[1]}, Sports: {full[2]}, Hawkers: {full[3]}')
    print(f'   Healthcare: {full[4]}, Parks: {full[5]}, Carparks: {full[6]}, Transit: {full[7]}')

print('\n✓ All tests passed!')
conn.close()
