from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .io import write_xlsx

INPUT_DIR = Path("input")


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    industry: str
    columns: list[str]
    key_column: str
    embed_columns: list[str]
    suggested_model: str
    steps: list[str]
    rows: list[dict[str, object]]


TEMPLATES: list[Template] = [
    Template(
        id="vendor-dedup",
        name="Vendor Deduplication After Merger",
        description=(
            "Two companies merged and now have overlapping vendor lists. "
            "Find duplicate vendors across both systems despite different name spellings."
        ),
        industry="Procurement / M&A",
        columns=["Vendor ID", "Company Name", "Address", "Category", "Annual Spend"],
        key_column="Vendor ID",
        embed_columns=["Company Name"],
        suggested_model="entity",
        steps=[
            "Copy this template to input/ with: index-numerorum templates --use vendor-dedup",
            "Run: index-numerorum --quick",
            'The wizard auto-detects "Company Name" and assigns the entity model',
            "Open the output xlsx -- rows with similarity > 0.85 are likely the same vendor",
            "Review and merge duplicates in your procurement system",
        ],
        rows=[
            {
                "Vendor ID": "V-1001",
                "Company Name": "Acme Corporation",
                "Address": "100 Industrial Way, Springfield, IL",
                "Category": "Raw Materials",
                "Annual Spend": 245000,
            },
            {
                "Vendor ID": "V-1002",
                "Company Name": "Acme Corp",
                "Address": "100 Industrial Way, Springfield, IL",
                "Category": "Raw Materials",
                "Annual Spend": 245000,
            },
            {
                "Vendor ID": "V-1003",
                "Company Name": "Acme Inc.",
                "Address": "100 Industrial Pkwy, Springfield, IL",
                "Category": "Raw Materials",
                "Annual Spend": 128000,
            },
            {
                "Vendor ID": "V-1004",
                "Company Name": "GlobalTech Solutions LLC",
                "Address": "500 Tech Blvd, Austin, TX",
                "Category": "IT Services",
                "Annual Spend": 890000,
            },
            {
                "Vendor ID": "V-1005",
                "Company Name": "Global Tech Solutions",
                "Address": "500 Technology Blvd, Austin, TX",
                "Category": "IT Services",
                "Annual Spend": 890000,
            },
            {
                "Vendor ID": "V-1006",
                "Company Name": "GloblTech Solns Ltd",
                "Address": "500 Tech Blvd Ste 200, Austin, TX",
                "Category": "IT Services",
                "Annual Spend": 340000,
            },
            {
                "Vendor ID": "V-1007",
                "Company Name": "Midwest Paper Company",
                "Address": "42 Mill Road, Gary, IN",
                "Category": "Office Supplies",
                "Annual Spend": 67000,
            },
            {
                "Vendor ID": "V-1008",
                "Company Name": "Midwest Paper Co.",
                "Address": "42 Mill Rd, Gary, Indiana",
                "Category": "Office Supplies",
                "Annual Spend": 67000,
            },
            {
                "Vendor ID": "V-1009",
                "Company Name": "Mid-West Paper & Supply",
                "Address": "42 Mill Road, Gary, IN",
                "Category": "Office Supplies",
                "Annual Spend": 23000,
            },
            {
                "Vendor ID": "V-1010",
                "Company Name": "Secure Logistics International",
                "Address": "789 Harbor Dr, Long Beach, CA",
                "Category": "Shipping",
                "Annual Spend": 1200000,
            },
            {
                "Vendor ID": "V-1011",
                "Company Name": "SecureLogistics Intl",
                "Address": "789 Harbor Drive, Long Beach, CA",
                "Category": "Shipping",
                "Annual Spend": 1200000,
            },
            {
                "Vendor ID": "V-1012",
                "Company Name": "Secure Logistics Int'l Inc",
                "Address": "789 Harbor Dr, Long Beach, CA",
                "Category": "Shipping",
                "Annual Spend": 540000,
            },
            {
                "Vendor ID": "V-1013",
                "Company Name": "Brightline Electrical Services",
                "Address": "330 Volt Ave, Reno, NV",
                "Category": "Maintenance",
                "Annual Spend": 185000,
            },
            {
                "Vendor ID": "V-1014",
                "Company Name": "Bright Line Electric",
                "Address": "330 Volt Avenue, Reno, NV",
                "Category": "Maintenance",
                "Annual Spend": 185000,
            },
            {
                "Vendor ID": "V-1015",
                "Company Name": "Precision Manufacturing Group",
                "Address": "1200 Factory St, Detroit, MI",
                "Category": "Raw Materials",
                "Annual Spend": 2100000,
            },
            {
                "Vendor ID": "V-1016",
                "Company Name": "Precision Mfg Group LLC",
                "Address": "1200 Factory Street, Detroit, MI",
                "Category": "Raw Materials",
                "Annual Spend": 2100000,
            },
            {
                "Vendor ID": "V-1017",
                "Company Name": "Precision Manufacturing Grp",
                "Address": "1200 Factory St, Detroit, Michigan",
                "Category": "Raw Materials",
                "Annual Spend": 980000,
            },
            {
                "Vendor ID": "V-1018",
                "Company Name": "CloudNine IT Partners",
                "Address": "77 Server Lane, Seattle, WA",
                "Category": "IT Services",
                "Annual Spend": 456000,
            },
            {
                "Vendor ID": "V-1019",
                "Company Name": "Cloud Nine IT Partners Inc",
                "Address": "77 Server Ln, Seattle, WA",
                "Category": "IT Services",
                "Annual Spend": 456000,
            },
            {
                "Vendor ID": "V-1020",
                "Company Name": "Cloud9 IT",
                "Address": "77 Server Lane, Seattle, WA",
                "Category": "IT Services",
                "Annual Spend": 178000,
            },
        ],
    ),
    Template(
        id="address-cleansing",
        name="Customer Address Cleansing",
        description=(
            "Customer database with address variants -- same location written "
            "different ways. Find and group matching addresses for deduplication."
        ),
        industry="CRM / Customer Data",
        columns=["Customer ID", "Full Name", "Address", "City", "State", "ZIP"],
        key_column="Customer ID",
        embed_columns=["Address"],
        suggested_model="address",
        steps=[
            "Copy this template to input/ with: index-numerorum templates --use address-cleansing",
            "Run: index-numerorum --quick",
            'The wizard auto-detects the "Address" column and assigns the address model',
            "Open the output -- rows with similarity > 0.90 share the same address",
            "Merge duplicate customer records in your CRM",
        ],
        rows=[
            {
                "Customer ID": "C-001",
                "Full Name": "John Smith",
                "Address": "123 Main Street, Apt 4B",
                "City": "Springfield",
                "State": "IL",
                "ZIP": 62701,
            },
            {
                "Customer ID": "C-002",
                "Full Name": "John Smyth",
                "Address": "123 Main St Apt 4B",
                "City": "Springfield",
                "State": "IL",
                "ZIP": 62701,
            },
            {
                "Customer ID": "C-003",
                "Full Name": "J. Smith",
                "Address": "123 Main St., #4B",
                "City": "Springfield",
                "State": "IL",
                "ZIP": 62701,
            },
            {
                "Customer ID": "C-004",
                "Full Name": "Maria Garcia",
                "Address": "456 Oak Avenue",
                "City": "Austin",
                "State": "TX",
                "ZIP": 78701,
            },
            {
                "Customer ID": "C-005",
                "Full Name": "Maria Garcia-Lopez",
                "Address": "456 Oak Ave",
                "City": "Austin",
                "State": "TX",
                "ZIP": 78701,
            },
            {
                "Customer ID": "C-006",
                "Full Name": "M Garcia",
                "Address": "456 Oak Ave, Unit 1",
                "City": "Austin",
                "State": "TX",
                "ZIP": 78701,
            },
            {
                "Customer ID": "C-007",
                "Full Name": "Robert Johnson",
                "Address": "789 Elm Blvd, Suite 200",
                "City": "Denver",
                "State": "CO",
                "ZIP": 80202,
            },
            {
                "Customer ID": "C-008",
                "Full Name": "Bob Johnson",
                "Address": "789 Elm Boulevard Ste 200",
                "City": "Denver",
                "State": "CO",
                "ZIP": 80202,
            },
            {
                "Customer ID": "C-009",
                "Full Name": "Sarah Chen",
                "Address": "321 Pine Road",
                "City": "Portland",
                "State": "OR",
                "ZIP": 97201,
            },
            {
                "Customer ID": "C-010",
                "Full Name": "S. Chen",
                "Address": "321 Pine Rd",
                "City": "Portland",
                "State": "OR",
                "ZIP": 97201,
            },
            {
                "Customer ID": "C-011",
                "Full Name": "Sarah Chen",
                "Address": "321 Pine Rd.",
                "City": "Portland",
                "State": "OR",
                "ZIP": 97201,
            },
            {
                "Customer ID": "C-012",
                "Full Name": "David Williams",
                "Address": "555 Maple Dr, Floor 3",
                "City": "Chicago",
                "State": "IL",
                "ZIP": 60601,
            },
            {
                "Customer ID": "C-013",
                "Full Name": "Dave Williams",
                "Address": "555 Maple Drive Fl 3",
                "City": "Chicago",
                "State": "IL",
                "ZIP": 60601,
            },
            {
                "Customer ID": "C-014",
                "Full Name": "Emily Davis",
                "Address": "888 Cedar Lane",
                "City": "Nashville",
                "State": "TN",
                "ZIP": 37201,
            },
            {
                "Customer ID": "C-015",
                "Full Name": "Em Davis",
                "Address": "888 Cedar Ln",
                "City": "Nashville",
                "State": "TN",
                "ZIP": 37201,
            },
            {
                "Customer ID": "C-016",
                "Full Name": "Emily Davis",
                "Address": "888 Cedar Ln.",
                "City": "Nashville",
                "State": "TN",
                "ZIP": 37201,
            },
            {
                "Customer ID": "C-017",
                "Full Name": "James Brown",
                "Address": "222 Birch Ct",
                "City": "Miami",
                "State": "FL",
                "ZIP": 33101,
            },
            {
                "Customer ID": "C-018",
                "Full Name": "Jim Brown",
                "Address": "222 Birch Court",
                "City": "Miami",
                "State": "FL",
                "ZIP": 33101,
            },
            {
                "Customer ID": "C-019",
                "Full Name": "Lisa Park",
                "Address": "444 Walnut St, Bldg A",
                "City": "San Jose",
                "State": "CA",
                "ZIP": 95101,
            },
            {
                "Customer ID": "C-020",
                "Full Name": "L Park",
                "Address": "444 Walnut Street Building A",
                "City": "San Jose",
                "State": "CA",
                "ZIP": 95101,
            },
        ],
    ),
    Template(
        id="product-catalog",
        name="Product Catalog Deduplication",
        description=(
            "E-commerce product catalog with duplicate listings from multiple suppliers. "
            "Find products that are the same item listed under different names."
        ),
        industry="E-Commerce / Retail",
        columns=["SKU", "Product Name", "Description", "Category", "Price"],
        key_column="SKU",
        embed_columns=["Product Name", "Description"],
        suggested_model="mini",
        steps=[
            "Copy this template to input/ with: index-numerorum templates --use product-catalog",
            "Run: index-numerorum --quick",
            "The wizard embeds both Product Name and Description, averaged together",
            "Open the output -- rows with similarity > 0.90 are likely duplicate products",
            "Consolidate SKUs and update your catalog",
        ],
        rows=[
            {
                "SKU": "EL-001",
                "Product Name": "Wireless Bluetooth Mouse",
                "Description": "Ergonomic wireless mouse with Bluetooth 5.0 connectivity",
                "Category": "Electronics",
                "Price": 29.99,
            },
            {
                "SKU": "EL-002",
                "Product Name": "BT Cordless Mouse",
                "Description": "Ergonomic wireless mouse with Bluetooth",
                "Category": "Electronics",
                "Price": 28.99,
            },
            {
                "SKU": "EL-003",
                "Product Name": "Bluetooth Wireless Mouse",
                "Description": "Ergonomic bluetooth mouse wireless",
                "Category": "Electronics",
                "Price": 31.49,
            },
            {
                "SKU": "EL-004",
                "Product Name": "USB-C Charging Hub 7-in-1",
                "Description": "7 port USB C hub with HDMI ethernet and USB 3.0",
                "Category": "Electronics",
                "Price": 49.99,
            },
            {
                "SKU": "EL-005",
                "Product Name": "7-Port USB Type-C Hub",
                "Description": "USB-C hub with 7 ports including HDMI and ethernet",
                "Category": "Electronics",
                "Price": 47.99,
            },
            {
                "SKU": "OF-001",
                "Product Name": "Standing Desk Anti-Fatigue Mat",
                "Description": "Extra thick cushioned floor mat for standing desks",
                "Category": "Office",
                "Price": 39.99,
            },
            {
                "SKU": "OF-002",
                "Product Name": "Ergonomic Floor Mat for Standing",
                "Description": "Anti-fatigue cushioned mat for stand-up desk use",
                "Category": "Office",
                "Price": 41.99,
            },
            {
                "SKU": "OF-003",
                "Product Name": "Comfort Standing Mat",
                "Description": "Thick cushioned mat for standing desks anti-fatigue",
                "Category": "Office",
                "Price": 37.99,
            },
            {
                "SKU": "OF-004",
                "Product Name": "Bamboo Desk Organizer",
                "Description": "Wooden desktop organizer with 6 compartments and drawer",
                "Category": "Office",
                "Price": 34.99,
            },
            {
                "SKU": "OF-005",
                "Product Name": "Desktop Organizer Bamboo",
                "Description": "Bamboo desk organizer with drawer and compartments",
                "Category": "Office",
                "Price": 36.49,
            },
            {
                "SKU": "KT-001",
                "Product Name": "Japanese Steel Chef Knife Set",
                "Description": "6-piece knife block set with Japanese stainless steel blades",
                "Category": "Kitchen",
                "Price": 89.99,
            },
            {
                "SKU": "KT-002",
                "Product Name": "6-Piece Knife Block Set",
                "Description": "Japanese steel chef knives with wooden block",
                "Category": "Kitchen",
                "Price": 92.99,
            },
            {
                "SKU": "KT-003",
                "Product Name": "Digital Air Fryer 5.8 Qt",
                "Description": "5.8 quart air fryer with digital presets and rapid air circulation",
                "Category": "Kitchen",
                "Price": 79.99,
            },
            {
                "SKU": "KT-004",
                "Product Name": "Air Fryer with Digital Display",
                "Description": "Digital airfryer 5.8 quart with preset cooking programs",
                "Category": "Kitchen",
                "Price": 82.49,
            },
            {
                "SKU": "SP-001",
                "Product Name": "Premium Yoga Mat Extra Thick",
                "Description": "Non-slip exercise mat extra thick for yoga and pilates",
                "Category": "Sports",
                "Price": 24.99,
            },
            {
                "SKU": "SP-002",
                "Product Name": "Thick Non-Slip Exercise Mat",
                "Description": "Extra thick yoga mat non-slip for exercise and pilates",
                "Category": "Sports",
                "Price": 26.99,
            },
            {
                "SKU": "SP-003",
                "Product Name": "Resistance Band Set of 5",
                "Description": "Set of 5 latex loop resistance bands for strength training",
                "Category": "Sports",
                "Price": 19.99,
            },
            {
                "SKU": "SP-004",
                "Product Name": "5-Piece Latex Loop Bands",
                "Description": "Resistance bands set of 5 for workout and strength training",
                "Category": "Sports",
                "Price": 18.49,
            },
            {
                "SKU": "SP-005",
                "Product Name": "Insulated Water Bottle 32oz",
                "Description": "Stainless steel vacuum insulated water bottle 32 oz",
                "Category": "Sports",
                "Price": 22.99,
            },
            {
                "SKU": "SP-006",
                "Product Name": "32 oz Stainless Steel Bottle",
                "Description": "Vacuum insulated stainless steel water bottle",
                "Category": "Sports",
                "Price": 21.99,
            },
        ],
    ),
    Template(
        id="lead-dedup",
        name="Sales Lead Deduplication",
        description=(
            "Sales team has duplicate leads from multiple campaigns. "
            "Find leads from the same company to consolidate outreach."
        ),
        industry="Sales / CRM",
        columns=["Lead ID", "Company", "Contact Name", "Title", "Notes"],
        key_column="Lead ID",
        embed_columns=["Company", "Notes"],
        suggested_model="entity",
        steps=[
            "Copy this template to input/ with: index-numerorum templates --use lead-dedup",
            "Run: index-numerorum --quick",
            'The wizard auto-detects "Company" and assigns the entity model',
            "Open the output -- leads with similarity > 0.85 are likely the same company",
            "Consolidate leads before outreach to avoid duplicate contacts",
        ],
        rows=[
            {
                "Lead ID": "L-001",
                "Company": "Apex Technologies Inc",
                "Contact Name": "Sarah Mitchell",
                "Title": "CTO",
                "Notes": "Interested in enterprise security solution",
            },
            {
                "Lead ID": "L-002",
                "Company": "Apex Technology",
                "Contact Name": "Sarah Mitchell",
                "Title": "Chief Technology Officer",
                "Notes": "Enterprise security product inquiry",
            },
            {
                "Lead ID": "L-003",
                "Company": "Apex Tech Inc.",
                "Contact Name": "James Mitchell",
                "Title": "VP Engineering",
                "Notes": "Wants security demo for engineering team",
            },
            {
                "Lead ID": "L-004",
                "Company": "Blue Harbor Financial",
                "Contact Name": "David Park",
                "Title": "CFO",
                "Notes": "Looking for compliance automation tools",
            },
            {
                "Lead ID": "L-005",
                "Company": "Blue Harbor Financial Services",
                "Contact Name": "D. Park",
                "Title": "Chief Financial Officer",
                "Notes": "Compliance tool evaluation",
            },
            {
                "Lead ID": "L-006",
                "Company": "BlueHarbor Finance",
                "Contact Name": "Linda Park",
                "Title": "Finance Director",
                "Notes": "Needs automated compliance reporting",
            },
            {
                "Lead ID": "L-007",
                "Company": "NovaCare Health Systems",
                "Contact Name": "Rachel Adams",
                "Title": "VP Operations",
                "Notes": "Evaluating patient scheduling software",
            },
            {
                "Lead ID": "L-008",
                "Company": "Nova Care Health",
                "Contact Name": "R. Adams",
                "Title": "Operations VP",
                "Notes": "Patient scheduling system demo request",
            },
            {
                "Lead ID": "L-009",
                "Company": "Summit Retail Group",
                "Contact Name": "Mark Thompson",
                "Title": "Director of IT",
                "Notes": "Needs POS integration with inventory management",
            },
            {
                "Lead ID": "L-010",
                "Company": "Summit Retail Grp LLC",
                "Contact Name": "M. Thompson",
                "Title": "IT Director",
                "Notes": "Point of sale inventory integration inquiry",
            },
            {
                "Lead ID": "L-011",
                "Company": "Summit Retail",
                "Contact Name": "Karen Thompson",
                "Title": "IT Manager",
                "Notes": "POS and inventory management system",
            },
            {
                "Lead ID": "L-012",
                "Company": "Ironclad Construction",
                "Contact Name": "Tom Rivera",
                "Title": "Project Manager",
                "Notes": "Looking for project management and bidding software",
            },
            {
                "Lead ID": "L-013",
                "Company": "Iron Clad Construction Co",
                "Contact Name": "Thomas Rivera",
                "Title": "PM",
                "Notes": "Project management software for construction bidding",
            },
            {
                "Lead ID": "L-014",
                "Company": "Pinnacle Logistics",
                "Contact Name": "Amy Chen",
                "Title": "COO",
                "Notes": "Fleet tracking and route optimization platform",
            },
            {
                "Lead ID": "L-015",
                "Company": "Pinnacle Logistics Corp",
                "Contact Name": "A. Chen",
                "Title": "Chief Operating Officer",
                "Notes": "Route optimization and fleet management",
            },
            {
                "Lead ID": "L-016",
                "Company": "Pinnacle Logitics",
                "Contact Name": "Wei Chen",
                "Title": "Operations Manager",
                "Notes": "Fleet tracking platform evaluation",
            },
            {
                "Lead ID": "L-017",
                "Company": "Evergreen Education Partners",
                "Contact Name": "Nancy Liu",
                "Title": "Superintendent",
                "Notes": "Student information system migration",
            },
            {
                "Lead ID": "L-018",
                "Company": "Evergreen Ed Partners",
                "Contact Name": "N. Liu",
                "Title": "District Superintendent",
                "Notes": "SIS migration and student data management",
            },
            {
                "Lead ID": "L-019",
                "Company": "Sterling Insurance Group",
                "Contact Name": "Paul Martinez",
                "Title": "Risk Manager",
                "Notes": "Claims processing automation evaluation",
            },
            {
                "Lead ID": "L-020",
                "Company": "Sterling Insurance Grp",
                "Contact Name": "P. Martinez",
                "Title": "Risk Mgmt",
                "Notes": "Automated claims processing system",
            },
        ],
    ),
    Template(
        id="counterparty-screening",
        name="Counterparty Entity Resolution",
        description=(
            "Compliance and risk teams need to match entity names across internal records, "
            "watchlists, and vendor files despite inconsistent naming."
        ),
        industry="Finance / Compliance",
        columns=["Entity ID", "Legal Name", "DBA Name", "Country", "Risk Score"],
        key_column="Entity ID",
        embed_columns=["Legal Name", "DBA Name"],
        suggested_model="entity",
        steps=[
            "Copy this template to input/: index-numerorum templates --use counterparty-screening",
            "Run: index-numerorum --quick",
            'The wizard auto-detects "Legal Name" and assigns the entity model',
            "Open the output -- entities with similarity > 0.85 may be the same counterparty",
            "Flag high-risk matches for compliance review",
        ],
        rows=[
            {
                "Entity ID": "E-001",
                "Legal Name": "Meridian Capital Holdings Ltd",
                "DBA Name": "Meridian Capital",
                "Country": "United Kingdom",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-002",
                "Legal Name": "Meridian Capital Holdings Limited",
                "DBA Name": "Meridian Cap",
                "Country": "UK",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-003",
                "Legal Name": "Meridian Cap Holdings",
                "DBA Name": "Meridian Capital Management",
                "Country": "United Kingdom",
                "Risk Score": "High",
            },
            {
                "Entity ID": "E-004",
                "Legal Name": "Sakura Trading Co. Ltd",
                "DBA Name": "Sakura Trading",
                "Country": "Japan",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-005",
                "Legal Name": "Sakura Trading Company Limited",
                "DBA Name": "Sakura Trade Co",
                "Country": "Japan",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-006",
                "Legal Name": "Atlas Energy Partners LLC",
                "DBA Name": "Atlas Energy",
                "Country": "United States",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-007",
                "Legal Name": "Atlas Energy Partners",
                "DBA Name": "Atlas Energy Group",
                "Country": "USA",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-008",
                "Legal Name": "Atlas Energy Ptnrs LLC",
                "DBA Name": "Atlas E&P",
                "Country": "United States",
                "Risk Score": "High",
            },
            {
                "Entity ID": "E-009",
                "Legal Name": "Vanguard Shipping International SA",
                "DBA Name": "Vanguard Shipping",
                "Country": "Panama",
                "Risk Score": "High",
            },
            {
                "Entity ID": "E-010",
                "Legal Name": "Vanguard Shipping Intl S.A.",
                "DBA Name": "Vanguard Ship Intl",
                "Country": "Panama",
                "Risk Score": "High",
            },
            {
                "Entity ID": "E-011",
                "Legal Name": "Phoenix Pharma GmbH",
                "DBA Name": "Phoenix Pharmaceuticals",
                "Country": "Germany",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-012",
                "Legal Name": "Phoenix Pharma AG",
                "DBA Name": "Phoenix Pharma",
                "Country": "Switzerland",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-013",
                "Legal Name": "Phoenix Pharmaceuticals GmbH",
                "DBA Name": "Phoenix Pharma Germany",
                "Country": "Germany",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-014",
                "Legal Name": "Oceanic Mining Corporation",
                "DBA Name": "Oceanic Mining",
                "Country": "Australia",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-015",
                "Legal Name": "Oceanic Mining Corp",
                "DBA Name": "Oceanic Mine Corp",
                "Country": "Australia",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-016",
                "Legal Name": "Nordic Biotech A/S",
                "DBA Name": "Nordic Bio",
                "Country": "Denmark",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-017",
                "Legal Name": "Nordic Biotech AB",
                "DBA Name": "Nordic Biotech",
                "Country": "Sweden",
                "Risk Score": "Low",
            },
            {
                "Entity ID": "E-018",
                "Legal Name": "Pacific Rim Ventures Inc",
                "DBA Name": "Pacific Rim Ventures",
                "Country": "Singapore",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-019",
                "Legal Name": "Pacific Rim Ventures Pte Ltd",
                "DBA Name": "Pacific Rim Capital",
                "Country": "Singapore",
                "Risk Score": "Medium",
            },
            {
                "Entity ID": "E-020",
                "Legal Name": "Pacific Rim Venture Inc.",
                "DBA Name": "PRV Capital",
                "Country": "Singapore",
                "Risk Score": "High",
            },
        ],
    ),
]


def get_template(template_id: str) -> Template | None:
    for t in TEMPLATES:
        if t.id == template_id:
            return t
    return None


def list_templates() -> list[Template]:
    return list(TEMPLATES)


def copy_template(template_id: str, dest: Path | None = None) -> Path:
    template = get_template(template_id)
    if template is None:
        raise ValueError(f"Unknown template: {template_id}")
    dest_dir = dest or INPUT_DIR
    dest_dir.mkdir(exist_ok=True)
    dest_path = dest_dir / f"{template_id}.xlsx"
    df = pd.DataFrame(template.rows, columns=template.columns)
    metadata = {
        "template": template.id,
        "name": template.name,
        "key_column": template.key_column,
        "embed_columns": ", ".join(template.embed_columns),
        "suggested_model": template.suggested_model,
    }
    write_xlsx(df, dest_path, metadata=metadata, overwrite=True)
    return dest_path
