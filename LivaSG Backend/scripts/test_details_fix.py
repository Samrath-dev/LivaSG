import sqlite3

conn = sqlite3.connect('street_geocode.db')
c = conn.cursor()

street_name = 'UPPER BUKIT TIMAH ROAD'

fac = c.execute(
    'SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks, transit FROM street_facilities WHERE street_name = ?',
    (street_name,)
).fetchone()

print(f'Query result: {fac}')

if fac:
    schools, sports, hawkers, healthcare, parks, carparks, transit = fac
    print(f'\nUnpacked successfully:')
    print(f'  schools={schools}')
    print(f'  sports={sports}')
    print(f'  hawkers={hawkers}')
    print(f'  healthcare={healthcare}')
    print(f'  parks={parks}')
    print(f'  carparks={carparks}')
    print(f'  transit={transit}')
    print('\n✓ Fix verified - query now includes transit column')
else:
    print('ERROR: No data found')

conn.close()
