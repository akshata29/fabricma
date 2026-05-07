"""
seed_data_generator.py

Generates 11 seed CSV files for Meridian Supply Co. (US wholesale distributor).
Uses Python stdlib only: csv, random, datetime, os.  No external dependencies.

Run once locally, then upload CSVs to Fabric lakehouse.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fabric', 'seed_data')

DATE_START = date(2022, 1, 1)
DATE_END = date(2024, 12, 31)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def rand_date_str(start: date, end: date) -> str:
    return rand_date(start, end).isoformat()


def write_csv(filename: str, fieldnames: list, rows: list) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f'  {filename}: {len(rows):,} rows')


def open_csv_writer(filename: str, fieldnames: list):
    """Return (file_handle, DictWriter) for streaming large tables."""
    path = os.path.join(OUTPUT_DIR, filename)
    fh = open(path, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    return fh, writer


# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

CURRENCIES = [
    ('USD', 'US Dollar',          '$'),
    ('EUR', 'Euro',               '\u20ac'),
    ('GBP', 'British Pound',      '\u00a3'),
    ('CAD', 'Canadian Dollar',    'CA$'),
    ('MXN', 'Mexican Peso',       'MX$'),
    ('JPY', 'Japanese Yen',       '\u00a5'),
    ('CNY', 'Chinese Yuan',       '\u00a5'),
    ('AUD', 'Australian Dollar',  'A$'),
    ('BRL', 'Brazilian Real',     'R$'),
    ('CHF', 'Swiss Franc',        'CHF'),
    ('SEK', 'Swedish Krona',      'kr'),
    ('INR', 'Indian Rupee',       '\u20b9'),
]

TERRITORIES = [
    (1,  'Northeast',        'East',          'Patricia Nguyen'),
    (2,  'Mid-Atlantic',     'East',          'Robert Kim'),
    (3,  'Southeast',        'South',         'Sandra Williams'),
    (4,  'Great Lakes',      'Midwest',       'Thomas Baker'),
    (5,  'Plains',           'Midwest',       'Laura Chen'),
    (6,  'Southwest',        'South',         'Michael Torres'),
    (7,  'Mountain',         'West',          'Jennifer Davis'),
    (8,  'Pacific Northwest','West',          'David Martinez'),
    (9,  'California',       'West',          'Emily Johnson'),
    (10, 'International',    'International', 'Christopher Lee'),
]

WAREHOUSES = [
    (1, 'Northeast DC',       'Edison',       'NJ', 50000),
    (2, 'Mid-Atlantic Hub',   'Baltimore',    'MD', 40000),
    (3, 'Southeast DC',       'Atlanta',      'GA', 45000),
    (4, 'Great Lakes DC',     'Columbus',     'OH', 48000),
    (5, 'Central Hub',        'Kansas City',  'MO', 60000),
    (6, 'Southwest DC',       'Dallas',       'TX', 55000),
    (7, 'Mountain DC',        'Denver',       'CO', 35000),
    (8, 'West Coast DC',      'Los Angeles',  'CA', 70000),
]

# (state_code, territory_id)
STATES = [
    ('AL', 3), ('GA', 3), ('FL', 3), ('SC', 3), ('NC', 3),
    ('NY', 1), ('CT', 1), ('MA', 1), ('NJ', 1),
    ('PA', 2), ('MD', 2), ('VA', 2), ('DE', 2),
    ('OH', 4), ('MI', 4), ('IL', 4), ('IN', 4), ('WI', 4),
    ('MN', 5), ('IA', 5), ('MO', 5), ('KS', 5), ('NE', 5),
    ('TX', 6), ('OK', 6), ('AR', 6), ('LA', 6),
    ('CO', 7), ('UT', 7), ('NM', 7), ('AZ', 7), ('NV', 7),
    ('WA', 8), ('OR', 8), ('ID', 8), ('MT', 8),
    ('CA', 9),
]

CITIES_BY_STATE = {
    'AL': ['Birmingham', 'Montgomery', 'Huntsville'],
    'GA': ['Atlanta', 'Savannah', 'Augusta'],
    'FL': ['Miami', 'Tampa', 'Orlando', 'Jacksonville'],
    'SC': ['Charleston', 'Columbia'],
    'NC': ['Charlotte', 'Raleigh', 'Durham'],
    'NY': ['New York', 'Buffalo', 'Albany', 'Rochester'],
    'CT': ['Hartford', 'Bridgeport', 'New Haven'],
    'MA': ['Boston', 'Worcester', 'Springfield'],
    'NJ': ['Newark', 'Jersey City', 'Trenton'],
    'PA': ['Philadelphia', 'Pittsburgh', 'Allentown'],
    'MD': ['Baltimore', 'Rockville', 'Annapolis'],
    'VA': ['Richmond', 'Norfolk', 'Virginia Beach'],
    'DE': ['Wilmington', 'Dover'],
    'OH': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo'],
    'MI': ['Detroit', 'Grand Rapids', 'Ann Arbor'],
    'IL': ['Chicago', 'Springfield', 'Rockford'],
    'IN': ['Indianapolis', 'Fort Wayne', 'Evansville'],
    'WI': ['Milwaukee', 'Madison', 'Green Bay'],
    'MN': ['Minneapolis', 'Saint Paul', 'Rochester'],
    'IA': ['Des Moines', 'Cedar Rapids', 'Davenport'],
    'MO': ['Kansas City', 'Saint Louis', 'Springfield'],
    'KS': ['Wichita', 'Overland Park', 'Kansas City'],
    'NE': ['Omaha', 'Lincoln', 'Bellevue'],
    'TX': ['Houston', 'Dallas', 'Austin', 'San Antonio', 'Fort Worth'],
    'OK': ['Oklahoma City', 'Tulsa'],
    'AR': ['Little Rock', 'Fort Smith'],
    'LA': ['New Orleans', 'Baton Rouge', 'Shreveport'],
    'CO': ['Denver', 'Colorado Springs', 'Aurora'],
    'UT': ['Salt Lake City', 'Provo', 'Ogden'],
    'NM': ['Albuquerque', 'Santa Fe', 'Las Cruces'],
    'AZ': ['Phoenix', 'Tucson', 'Scottsdale', 'Tempe'],
    'NV': ['Las Vegas', 'Reno', 'Henderson'],
    'WA': ['Seattle', 'Spokane', 'Tacoma'],
    'OR': ['Portland', 'Eugene', 'Salem'],
    'ID': ['Boise', 'Nampa', 'Meridian'],
    'MT': ['Billings', 'Missoula', 'Great Falls'],
    'CA': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'San Jose'],
}

FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Lisa', 'Daniel', 'Nancy',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Dorothy', 'Paul', 'Kimberly', 'Andrew', 'Emily', 'Kenneth', 'Donna',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
    'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
    'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
]

COMPANY_WORDS = [
    'Apex', 'Atlas', 'Blue', 'Bridge', 'Cardinal', 'Central', 'Core', 'Crown',
    'Delta', 'Dynamic', 'Eagle', 'East', 'Elite', 'Empire', 'Excel', 'Falcon',
    'First', 'Fort', 'Global', 'Golden', 'Grand', 'Great', 'Green', 'Heritage',
    'Highland', 'Horizon', 'Keystone', 'Liberty', 'Lincoln', 'Maple', 'Metro',
    'Midwest', 'National', 'North', 'Oak', 'Pacific', 'Peak', 'Pioneer', 'Premier',
    'Prime', 'Quality', 'Ridge', 'Royal', 'Silver', 'South', 'Star', 'Summit',
    'Superior', 'Swift', 'Titan', 'Trans', 'United', 'Valley', 'Venture', 'Victory',
    'Vista', 'West', 'Western', 'White', 'Woodland',
]

COMPANY_SUFFIXES = [
    'Inc.', 'LLC', 'Corp.', 'Co.', 'Ltd.',
    'Industries', 'Group', 'Solutions', 'Enterprises', 'Supply',
]

CATEGORIES = {
    'Electrical': ['Wiring & Cable', 'Switches & Outlets', 'Lighting', 'Conduit & Fittings', 'Circuit Breakers'],
    'Plumbing':   ['Pipes & Fittings', 'Valves', 'Water Heaters', 'Fixtures', 'Pumps'],
    'HVAC':       ['Ductwork', 'Filters', 'Thermostats', 'Compressors', 'Ventilation'],
    'Safety':     ['PPE', 'Fire Protection', 'Signage', 'First Aid', 'Fall Protection'],
    'Fasteners':  ['Bolts & Nuts', 'Screws', 'Anchors', 'Rivets', 'Washers'],
    'Tools':      ['Hand Tools', 'Power Tools', 'Measuring', 'Cutting', 'Clamping'],
    'Packaging':  ['Boxes', 'Pallets', 'Strapping', 'Stretch Wrap', 'Labels'],
    'Chemicals':  ['Lubricants', 'Solvents', 'Adhesives', 'Cleaners', 'Coatings'],
}

PRODUCT_ADJECTIVES = [
    'Heavy-Duty', 'Industrial', 'Commercial', 'Premium', 'Standard',
    'Pro-Grade', 'Economy', 'High-Performance',
]

PRODUCT_UNITS = ['10-Pack', '25-Pack', '50-Pack', '100-Pack', 'Single', 'Box', 'Roll', 'Case']

SEGMENTS     = ['Enterprise', 'Mid-Market', 'Small Business', 'Government', 'Education']
PAYMENT_TERMS = ['Net 30', 'Net 60', 'Net 45', '2/10 Net 30', 'COD']
CREDIT_LIMITS = [10000, 25000, 50000, 100000, 250000, 500000]
SUPPLIER_COUNTRIES = ['USA', 'USA', 'USA', 'USA', 'Canada', 'Mexico', 'Germany', 'China', 'Japan', 'Taiwan']


# ---------------------------------------------------------------------------
# Dimension generators
# ---------------------------------------------------------------------------

def gen_dim_currency() -> list:
    rows = [
        {'currency_code': code, 'currency_name': name, 'symbol': symbol}
        for code, name, symbol in CURRENCIES
    ]
    write_csv('dim_currency.csv', ['currency_code', 'currency_name', 'symbol'], rows)
    return [r['currency_code'] for r in rows]


def gen_dim_territory() -> list:
    rows = [
        {'territory_id': tid, 'territory_name': name, 'region': region, 'manager_name': mgr}
        for tid, name, region, mgr in TERRITORIES
    ]
    write_csv('dim_territory.csv', ['territory_id', 'territory_name', 'region', 'manager_name'], rows)
    return [r['territory_id'] for r in rows]


def gen_dim_warehouse() -> list:
    rows = [
        {
            'warehouse_id': wid, 'warehouse_name': name, 'city': city,
            'state_province': state, 'capacity_units': cap,
        }
        for wid, name, city, state, cap in WAREHOUSES
    ]
    write_csv(
        'dim_warehouse.csv',
        ['warehouse_id', 'warehouse_name', 'city', 'state_province', 'capacity_units'],
        rows,
    )
    return [r['warehouse_id'] for r in rows]


def gen_dim_supplier(n: int = 50) -> list:
    rows = []
    used_names: set = set()
    for i in range(1, n + 1):
        # Unique company name
        while True:
            name = f'{random.choice(COMPANY_WORDS)} {random.choice(COMPANY_SUFFIXES)}'
            if name not in used_names:
                used_names.add(name)
                break
        country = random.choice(SUPPLIER_COUNTRIES)
        if country == 'USA':
            state_code, _ = random.choice(STATES)
            city = random.choice(CITIES_BY_STATE[state_code])
            addr_state = state_code
        else:
            city = 'International'
            addr_state = ''
        fname = random.choice(FIRST_NAMES).lower()
        lname = random.choice(LAST_NAMES).lower()
        domain = ''.join(c for c in name.lower() if c.isalnum())[:12]
        rows.append({
            'supplier_id':   i,
            'company_name':  name,
            'country':       country,
            'contact_email': f'{fname}.{lname}@{domain}.com',
            'address_city':  city,
            'address_state': addr_state,
        })
    write_csv(
        'dim_supplier.csv',
        ['supplier_id', 'company_name', 'country', 'contact_email', 'address_city', 'address_state'],
        rows,
    )
    return [r['supplier_id'] for r in rows]


def gen_dim_product(supplier_ids: list, n: int = 200) -> list:
    rows = []
    used_names: set = set()
    cat_list = list(CATEGORIES.keys())
    for i in range(1, n + 1):
        cat    = random.choice(cat_list)
        subcat = random.choice(CATEGORIES[cat])
        base   = f'{random.choice(PRODUCT_ADJECTIVES)} {subcat} {random.choice(PRODUCT_UNITS)}'
        pname  = base
        suffix = 0
        while pname in used_names:
            suffix += 1
            pname = f'{base} #{suffix}'
        used_names.add(pname)
        unit_cost   = round(random.uniform(2.0, 250.0), 2)
        list_price  = round(unit_cost * random.uniform(1.25, 2.10), 2)
        reorder_pt  = random.randint(10, 200)
        rows.append({
            'product_id':    i,
            'product_name':  pname,
            'category':      cat,
            'subcategory':   subcat,
            'unit_cost':     unit_cost,
            'list_price':    list_price,
            'reorder_point': reorder_pt,
            'supplier_id':   random.choice(supplier_ids),
        })
    write_csv(
        'dim_product.csv',
        ['product_id', 'product_name', 'category', 'subcategory',
         'unit_cost', 'list_price', 'reorder_point', 'supplier_id'],
        rows,
    )
    return rows  # full dicts needed for price lookups in fact tables


def gen_dim_customer(territory_ids: list, n: int = 500) -> list:
    rows = []
    used_names: set = set()
    for i in range(1, n + 1):
        while True:
            name = f'{random.choice(COMPANY_WORDS)} {random.choice(COMPANY_SUFFIXES)}'
            if name not in used_names:
                used_names.add(name)
                break
        state_code, terr_id = random.choice(STATES)
        city = random.choice(CITIES_BY_STATE[state_code])
        # terr_id from STATES covers 1-9; territory 10 (International) excluded for domestic customers
        rows.append({
            'customer_id':       i,
            'company_name':      name,
            'city':              city,
            'state_province':    state_code,
            'territory_id':      terr_id,
            'customer_segment':  random.choice(SEGMENTS),
            'payment_terms':     random.choice(PAYMENT_TERMS),
            'credit_limit':      float(random.choice(CREDIT_LIMITS)),
        })
    write_csv(
        'dim_customer.csv',
        ['customer_id', 'company_name', 'city', 'state_province',
         'territory_id', 'customer_segment', 'payment_terms', 'credit_limit'],
        rows,
    )
    return rows


def gen_dim_salesrep(territory_ids: list, n: int = 40) -> list:
    rows = []
    fn = FIRST_NAMES[:]
    ln = LAST_NAMES[:]
    random.shuffle(fn)
    random.shuffle(ln)
    quota_options = [500_000, 750_000, 1_000_000, 1_250_000, 1_500_000, 2_000_000]
    for i in range(1, n + 1):
        rows.append({
            'salesrep_id':   i,
            'first_name':    fn[(i - 1) % len(fn)],
            'last_name':     ln[(i - 1) % len(ln)],
            'territory_id':  territory_ids[(i - 1) % len(territory_ids)],
            'hire_date':     rand_date_str(date(2018, 1, 1), date(2023, 12, 31)),
            'quota_annual':  float(random.choice(quota_options)),
        })
    write_csv(
        'dim_salesrep.csv',
        ['salesrep_id', 'first_name', 'last_name', 'territory_id', 'hire_date', 'quota_annual'],
        rows,
    )
    return rows


# ---------------------------------------------------------------------------
# Fact generators
# ---------------------------------------------------------------------------

def gen_fact_invoice_header(
    customer_ids: list,
    supplier_ids: list,
    currency_codes: list,
    n: int = 8000,
) -> list:
    rows = []
    for i in range(1, n + 1):
        invoice_date = rand_date(DATE_START, DATE_END)
        days_due     = random.choice([30, 45, 60])
        due_date     = invoice_date + timedelta(days=days_due)
        # ~75 % of invoices are paid
        if random.random() < 0.75:
            payment_date = (invoice_date + timedelta(days=random.randint(5, days_due + 15))).isoformat()
        else:
            payment_date = ''
        rows.append({
            'invoice_id':    i,
            'customer_id':   random.choice(customer_ids),
            'supplier_id':   random.choice(supplier_ids),
            'invoice_date':  invoice_date.isoformat(),
            'due_date':      due_date.isoformat(),
            'payment_date':  payment_date,
            'invoice_type':  random.choice(['AR', 'AP']),
            'currency_code': random.choice(currency_codes),
            'total_amount':  round(random.uniform(500.0, 50_000.0), 2),
        })
    write_csv(
        'fact_invoice_header.csv',
        ['invoice_id', 'customer_id', 'supplier_id', 'invoice_date', 'due_date',
         'payment_date', 'invoice_type', 'currency_code', 'total_amount'],
        rows,
    )
    return [r['invoice_id'] for r in rows]


def gen_fact_invoice_lines(invoice_ids: list, product_rows: list, n: int = 35_000) -> None:
    fieldnames = ['invoice_id', 'line_num', 'product_id', 'quantity', 'unit_price', 'line_amount']
    fh, writer = open_csv_writer('fact_invoice_lines.csv', fieldnames)
    try:
        # Track current line number per invoice so (invoice_id, line_num) is unique
        line_nums: dict = {}
        for _ in range(n):
            inv_id   = random.choice(invoice_ids)
            line_nums[inv_id] = line_nums.get(inv_id, 0) + 1
            product  = random.choice(product_rows)
            quantity = random.randint(1, 100)
            unit_price  = round(product['list_price'] * random.uniform(0.85, 1.10), 2)
            line_amount = round(quantity * unit_price, 2)
            writer.writerow({
                'invoice_id':   inv_id,
                'line_num':     line_nums[inv_id],
                'product_id':   product['product_id'],
                'quantity':     quantity,
                'unit_price':   unit_price,
                'line_amount':  line_amount,
            })
    finally:
        fh.close()
    print(f'  fact_invoice_lines.csv: {n:,} rows')


def gen_fact_stock_movement(product_ids: list, warehouse_ids: list, n: int = 150_000) -> None:
    movement_types = ['RECEIPT', 'SHIPMENT', 'ADJUSTMENT', 'RETURN']
    fieldnames = ['movement_id', 'product_id', 'warehouse_id', 'movement_date', 'movement_type', 'quantity_delta']
    fh, writer = open_csv_writer('fact_stock_movement.csv', fieldnames)
    try:
        for i in range(1, n + 1):
            mtype = random.choice(movement_types)
            if mtype == 'RECEIPT':
                qty = random.randint(10, 500)
            elif mtype == 'SHIPMENT':
                qty = -random.randint(1, 200)
            elif mtype == 'ADJUSTMENT':
                qty = random.randint(-50, 50)
            else:  # RETURN
                qty = random.randint(1, 50)
            writer.writerow({
                'movement_id':    i,
                'product_id':     random.choice(product_ids),
                'warehouse_id':   random.choice(warehouse_ids),
                'movement_date':  rand_date_str(DATE_START, DATE_END),
                'movement_type':  mtype,
                'quantity_delta': qty,
            })
    finally:
        fh.close()
    print(f'  fact_stock_movement.csv: {n:,} rows')


def gen_fact_sales(
    customer_rows: list,
    product_rows: list,
    salesrep_rows: list,
    n: int = 50_000,
) -> None:
    # FK lookup maps
    cust_territory = {r['customer_id']: r['territory_id'] for r in customer_rows}
    customer_ids   = [r['customer_id'] for r in customer_rows]
    salesrep_ids   = [r['salesrep_id'] for r in salesrep_rows]

    discount_choices = [0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20]

    fieldnames = [
        'order_id', 'customer_id', 'product_id', 'salesrep_id', 'territory_id',
        'order_date', 'ship_date', 'quantity', 'unit_price',
        'discount_pct', 'extended_amount', 'cogs',
    ]
    fh, writer = open_csv_writer('fact_sales.csv', fieldnames)
    try:
        for i in range(1, n + 1):
            customer_id  = random.choice(customer_ids)
            territory_id = cust_territory[customer_id]
            product      = random.choice(product_rows)
            order_date   = rand_date(DATE_START, DATE_END)
            ship_date    = order_date + timedelta(days=random.randint(1, 14))
            quantity     = random.randint(1, 50)
            unit_price   = round(product['list_price'] * random.uniform(0.90, 1.05), 2)
            discount_pct = random.choice(discount_choices)
            extended_amt = round(quantity * unit_price * (1 - discount_pct), 2)
            cogs         = round(quantity * product['unit_cost'], 2)
            writer.writerow({
                'order_id':        i,
                'customer_id':     customer_id,
                'product_id':      product['product_id'],
                'salesrep_id':     random.choice(salesrep_ids),
                'territory_id':    territory_id,
                'order_date':      order_date.isoformat(),
                'ship_date':       ship_date.isoformat(),
                'quantity':        quantity,
                'unit_price':      unit_price,
                'discount_pct':    discount_pct,
                'extended_amount': extended_amt,
                'cogs':            cogs,
            })
    finally:
        fh.close()
    print(f'  fact_sales.csv: {n:,} rows')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ensure_dir(OUTPUT_DIR)
    print(f'Output directory: {os.path.realpath(OUTPUT_DIR)}')
    print('Generating Meridian Supply Co. seed data...')

    # --- Dimensions ---
    currency_codes = gen_dim_currency()
    territory_ids  = gen_dim_territory()
    warehouse_ids  = gen_dim_warehouse()
    supplier_ids   = gen_dim_supplier(n=50)
    product_rows   = gen_dim_product(supplier_ids, n=200)
    customer_rows  = gen_dim_customer(territory_ids, n=500)
    salesrep_rows  = gen_dim_salesrep(territory_ids, n=40)

    # --- Fact tables ---
    product_ids  = [r['product_id']  for r in product_rows]
    customer_ids = [r['customer_id'] for r in customer_rows]

    invoice_ids = gen_fact_invoice_header(customer_ids, supplier_ids, currency_codes, n=8_000)
    gen_fact_invoice_lines(invoice_ids, product_rows, n=35_000)
    gen_fact_stock_movement(product_ids, warehouse_ids, n=150_000)
    gen_fact_sales(customer_rows, product_rows, salesrep_rows, n=50_000)

    # --- Validation summary ---
    print('\nValidating output files...')
    expected = [
        'dim_currency.csv', 'dim_territory.csv', 'dim_warehouse.csv',
        'dim_supplier.csv', 'dim_product.csv', 'dim_customer.csv',
        'dim_salesrep.csv', 'fact_invoice_header.csv', 'fact_invoice_lines.csv',
        'fact_stock_movement.csv', 'fact_sales.csv',
    ]
    missing = [f for f in expected if not os.path.isfile(os.path.join(OUTPUT_DIR, f))]
    if missing:
        print(f'  ERROR - missing files: {missing}')
    else:
        print(f'  All {len(expected)} CSV files present.')
    print('Done.')


if __name__ == '__main__':
    main()
