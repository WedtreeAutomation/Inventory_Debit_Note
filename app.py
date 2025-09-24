import re
import streamlit as st
import xmlrpc.client
import os
from dotenv import load_dotenv
import pandas as pd
import time
from collections import defaultdict
from datetime import datetime
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Odoo Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

CONFIG = {
    'url': os.getenv('ODOO_URL'),
    'db': os.getenv('ODOO_DB'),
    'username': os.getenv('ODOO_USERNAME'),
    'password': os.getenv('ODOO_PASSWORD'),
    'damage_location_name': os.getenv('damage_location_name'),
    'hq_company_name': os.getenv('HQ_COMPANY_NAME'),
    'app_username': os.getenv('APP_USERNAME'),
    'app_password': os.getenv('APP_PASSWORD'),
}

# Enhanced Custom CSS for professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        padding-top: 1rem;
    }
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #6c757d;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.8rem;
        margin: 2.5rem 0 1.5rem 0;
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
    }
    
    /* Modern card styling */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.8rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .metric-title {
        font-size: 0.9rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    /* Status cards */
    .status-card {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        position: relative;
        overflow: hidden;
    }
    
    .status-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%);
        z-index: 1;
    }
    
    .status-card * {
        position: relative;
        z-index: 2;
    }
    
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left-color: #28a745;
        color: #155724;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-left-color: #ffc107;
        color: #856404;
    }
    
    .error-card {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left-color: #dc3545;
        color: #721c24;
    }
    
    .info-card {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left-color: #17a2b8;
        color: #0c5460;
    }
    
    /* Enhanced buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Primary button variant */
    .primary-btn {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3) !important;
    }
    
    .primary-btn:hover {
        background: linear-gradient(135deg, #218838 0%, #1ca085 100%) !important;
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4) !important;
    }
    
    /* Secondary button variant */
    .secondary-btn {
        background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
        box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3) !important;
    }
    
    /* Danger button variant */
    .danger-btn {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3) !important;
    }
    
    /* Connection status styling */
    .connection-status {
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .connected {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 2px solid #28a745;
    }
    
    .disconnected {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border: 2px solid #dc3545;
    }
    
    /* Enhanced sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    .sidebar-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Enhanced tables */
    .dataframe {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .dataframe thead {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f8fafc !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #e2e8f0 !important;
        transition: background-color 0.2s ease !important;
    }
    
    /* Progress bars */
    .stProgress .st-bo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #667eea;
        background-color: #f7fafc;
    }
    
    /* Enhanced multiselect */
    .stMultiSelect {
        border-radius: 8px;
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Custom animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .welcome-card h2 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .welcome-card p {
        font-size: 1.1rem;
        opacity: 0.9;
        line-height: 1.6;
    }
    
    /* Feature highlights */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-item {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        border-top: 4px solid #667eea;
    }
    
    .feature-item:hover {
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #64748b;
        line-height: 1.5;
    }
    
    /* Statistics display */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .stat-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }
    
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Action panel */
    .action-panel {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .action-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        padding: 3rem 0 2rem 0;
        margin-top: 4rem;
        border-top: 1px solid #e2e8f0;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    .footer-content {
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .footer-sub {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    .app-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: bold;
        margin: 0.5rem 0;
        width: 100%;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .app-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .app-button-inventory {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    }
    .app-button-inventory:hover {
        background: linear-gradient(135deg, #ee5a24 0%, #ff6b6b 100%);
    }
    .app-button-lot-debit {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
    }
    .app-button-lot-debit:hover {
        background: linear-gradient(135deg, #00a085 0%, #00b894 100%);
    }
    .app-button-lot-credit {
        background: linear-gradient(135deg, #fdcb6e 0%, #f39c12 100%);
    }
    .app-button-lot-credit:hover {
        background: linear-gradient(135deg, #f39c12 0%, #fdcb6e 100%);
    }
    .button-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .button-icon {
        font-size: 1.2rem;
    }
    a{
        text-decoration: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'odoo_connected' not in st.session_state:
    st.session_state.odoo_connected = False
if 'inventory_results' not in st.session_state:
    st.session_state.inventory_results = None
if 'return_results' not in st.session_state:
    st.session_state.return_results = None
if 'uid' not in st.session_state:
    st.session_state.uid = None
if 'models' not in st.session_state:
    st.session_state.models = None
if 'damaged_lots' not in st.session_state:
    st.session_state.damaged_lots = []
if 'approved_lots' not in st.session_state:
    st.session_state.approved_lots = []
if 'rejected_lots' not in st.session_state:
    st.session_state.rejected_lots = []
if 'processed_lots' not in st.session_state:
    st.session_state.processed_lots = {}  # This should be a dictionary, not a list
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None
if 'selected_damaged_lots' not in st.session_state:
    st.session_state.selected_damaged_lots = []
if 'select_all_damaged' not in st.session_state:
    st.session_state.select_all_damaged = False
if 'lot_details' not in st.session_state:
    st.session_state.lot_details = {}
if 'lot_po_mapping' not in st.session_state:
    st.session_state.lot_po_mapping = {}

def connect_to_odoo():
    """Connect to Odoo and store connection in session state"""
    try:
        common = xmlrpc.client.ServerProxy(f"{CONFIG['url']}/xmlrpc/2/common")
        uid = common.authenticate(CONFIG['db'], CONFIG['username'], CONFIG['password'], {})
        models = xmlrpc.client.ServerProxy(f"{CONFIG['url']}/xmlrpc/2/object")
        
        st.session_state.uid = uid
        st.session_state.models = models
        st.session_state.odoo_connected = True
        
        return True, "Connection successful!"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def get_product_details(lot_name):
    """Get detailed product information for a specific lot/serial number"""
    try:
        # Find the move line for this lot
        move_lines = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.move.line', 'search_read',
            [[('lot_id.name', '=', lot_name)]],
            {'fields': ['picking_id', 'product_id'], 'limit': 1}
        )
        
        if not move_lines:
            return None
            
        product_id = move_lines[0]['product_id'][0] if move_lines[0].get('product_id') else None
        picking_id = move_lines[0]['picking_id'][0] if move_lines[0].get('picking_id') else None
        
        if not product_id or not picking_id:
            return None
        
        # Get product details
        product = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'product.product', 'read',
            [product_id], {'fields': ['name', 'default_code', 'product_tmpl_id']}
        )
        
        if not product:
            return None
            
        # Get picking details (reference/name)
        picking = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.picking', 'read',
            [picking_id], {'fields': ['name', 'origin']}
        )
        
        if not picking:
            return None
            
        po_number = picking[0].get('origin', 'Not Found')
        reference = picking[0].get('name', 'Not Found')
        
        # Get purchase order details
        po_details = None
        if po_number and po_number != 'Not Found':
            po_records = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'purchase.order', 'search_read',
                [[('name', '=', po_number)]],
                {'fields': ['partner_id'], 'limit': 1}
            )
            
            if po_records:
                vendor_id = po_records[0].get('partner_id')[0] if po_records[0].get('partner_id') else None
                
                # Get vendor name
                if vendor_id:
                    vendor = st.session_state.models.execute_kw(
                        CONFIG['db'], st.session_state.uid, CONFIG['password'],
                        'res.partner', 'read',
                        [vendor_id], {'fields': ['name']}
                    )
                    vendor_name = vendor[0].get('name', 'Not Found') if vendor else 'Not Found'
                else:
                    vendor_name = 'Not Found'
                
                # Get purchase order line details (price, discount)
                po_lines = st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'purchase.order.line', 'search_read',
                    [[('order_id.name', '=', po_number), ('product_id', '=', product_id)]],
                    {'fields': ['price_unit', 'discount']}
                )
                
                if po_lines:
                    price_unit = po_lines[0].get('price_unit', 0)
                    discount = po_lines[0].get('discount', 0)
                    cost_price = price_unit * (1 - discount/100)
                else:
                    price_unit = 0
                    discount = 0
                    cost_price = 0
                
                po_details = {
                    'po_number': po_number,
                    'vendor': vendor_name,
                    'price_unit': price_unit,
                    'discount': discount,
                    'cost_price': cost_price
                }
        
        # Get product template for SKU
        product_template = None
        if product[0].get('product_tmpl_id'):
            template_id = product[0]['product_tmpl_id'][0]
            template = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'product.template', 'read',
                [template_id], {'fields': ['name']}
            )
            if template:
                product_template = template[0].get('name', 'Not Found')
        
        # Get location information
        quant_records = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.quant', 'search_read',
            [[('lot_id.name', '=', lot_name)]],
            {'fields': ['location_id']}
        )
        
        locations = []
        if quant_records:
            for q in quant_records:
                if q.get('location_id'):
                    locations.append(q['location_id'][1])
        
        product_name = product[0].get('name', 'Not Found')
        sku = product[0].get('default_code')

        if not sku or sku.lower() == "false" or sku.strip() == "":
            match = re.search(r'\s(\S+)$', product_name)
            if match:
                sku = match.group(1)
            else:
                sku = "Not Found"

        return {
            'lot_name': lot_name,
            'product_name': product_name,
            'sku': sku,
            'product_template': product_template,
            'reference': reference,
            'locations': locations,
            'discount': po_details.get('discount', 0) if po_details else 0,
            'po_details': po_details
        }
        
    except Exception as e:
        st.error(f"Error getting product details for {lot_name}: {str(e)}")
        return None

def check_inventory(lot_serials):
    """Check if lot/serial numbers are in damage stock with detailed information"""
    not_in_damage_stock = []
    in_damage_stock = []
    
    # Show progress for large datasets
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_lots = len([ls.strip() for ls in lot_serials if ls.strip()])
    processed = 0
    
    for lot in [ls.strip() for ls in lot_serials if ls.strip()]:
        processed += 1
        progress_bar.progress(processed / total_lots)
        status_text.text(f"Processing {processed} of {total_lots} lots...")
        
        # Get detailed product information
        product_details = get_product_details(lot)
        
        quant_records = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.quant', 'search_read',
            [[('lot_id.name', '=', lot)]],
            {'fields': ['lot_id', 'location_id']}
        )

        if quant_records:
            found_in_damage = any(q['location_id'][1] == CONFIG['damage_location_name'] for q in quant_records)
            
            # Get all locations for this lot
            locations = {q['location_id'][1] for q in quant_records if q['location_id']}
            
            if not found_in_damage:
                not_in_damage_stock.append({
                    'lot': lot, 
                    'location': ", ".join(locations) if locations else "Unknown",
                    'status': 'Not in Damage',
                    'details': product_details
                })
            else:
                in_damage_stock.append({
                    'lot': lot,
                    'location': CONFIG['damage_location_name'],
                    'status': 'In Damage',
                    'details': product_details
                })
                
                # Store details in session state for later use
                if product_details:
                    st.session_state.lot_details[lot] = product_details
        else:
            not_in_damage_stock.append({
                'lot': lot, 
                'location': "Not Found in stock.quant",
                'status': 'Not Found',
                'details': product_details
            })
    
    progress_bar.empty()
    status_text.empty()
    
    return not_in_damage_stock, in_damage_stock

def get_po_for_lot(lot_name):
    """Get the PO number for a specific lot/serial number"""
    try:
        # Find the move line for this lot
        move_lines = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.move.line', 'search_read',
            [[('lot_id.name', '=', lot_name)]],
            {'fields': ['picking_id'], 'limit': 1}
        )
        
        if move_lines and move_lines[0].get('picking_id'):
            picking_id = move_lines[0]['picking_id'][0]
            
            # Get the picking details
            picking = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.picking', 'read',
                [picking_id], {'fields': ['origin']}
            )
            
            if picking and picking[0].get('origin'):
                return picking[0]['origin']
        
        return "Not Found"
    except Exception as e:
        return f"Error: {str(e)}"

def process_product_return(lot_serials):
    """
    Process product returns grouped by (PO, product).
    ✅ Uses Damage/Stock as source location (like product_return.py).
    """
    unique_lots = list(set(lot_serials))
    if not unique_lots:
        return False, "No Lot/Serial numbers entered."

    results = {}

    # Group lots by (PO, product)
    lot_groups = defaultdict(list)
    lot_move_data = {}

    for lot in unique_lots:
        try:
            po_number = get_po_for_lot(lot)
            if po_number.startswith("Error:") or po_number == "Not Found":
                results[lot] = {'success': False, 'message': f"Cannot process return: {po_number}"}
                continue

            move_lines = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.move.line', 'search_read',
                [[['lot_id.name', '=', lot]]],
                {'fields': ['id', 'product_id', 'lot_id', 'picking_id']}
            )
            if not move_lines:
                results[lot] = {'success': False, 'message': f"No move line found for lot: {lot}"}
                continue

            move_line = move_lines[0]
            product_id = move_line['product_id'][0]
            lot_groups[(po_number, product_id)].append(lot)
            lot_move_data[lot] = move_line

        except Exception as e:
            results[lot] = {'success': False, 'message': f"Error preparing lot: {str(e)}"}

    # Fetch company ID for filtering locations
    company_id = st.session_state.models.execute_kw(
        CONFIG['db'], st.session_state.uid, CONFIG['password'],
        'res.company', 'search_read',
        [[['name', '=', CONFIG['hq_company_name']]]],
        {'fields': ['id'], 'limit': 1}
    )[0]['id']

    # Find Damage/Stock Location (same as product_return.py)
    damage_location = st.session_state.models.execute_kw(
        CONFIG['db'], st.session_state.uid, CONFIG['password'],
        'stock.location', 'search_read',
        [[['complete_name', 'ilike', 'Damge/Stock'], ['company_id', '=', company_id]]],
        {'fields': ['id'], 'limit': 1}
    )
    if not damage_location:
        return False, f"Damage location 'Damge/Stock' not found in Odoo!"
    damage_location_id = damage_location[0]['id']

    # Process each (PO, product) group
    for (po_number, product_id), lots in lot_groups.items():
        try:
            picking_id = lot_move_data[lots[0]]['picking_id'][0]

            # Create return wizard
            wizard_id = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.return.picking', 'create', [{'picking_id': picking_id}]
            )

            # Update wizard lines
            return_lines = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.return.picking.line', 'search_read',
                [[['wizard_id', '=', wizard_id]]],
                {'fields': ['id', 'product_id']}
            )
            for line in return_lines:
                if line['product_id'][0] == product_id:
                    st.session_state.models.execute_kw(
                        CONFIG['db'], st.session_state.uid, CONFIG['password'],
                        'stock.return.picking.line', 'write',
                        [[line['id']], {'quantity': len(lots)}]
                    )
                else:
                    st.session_state.models.execute_kw(
                        CONFIG['db'], st.session_state.uid, CONFIG['password'],
                        'stock.return.picking.line', 'unlink', [[line['id']]]
                    )

            # Confirm return → create return picking
            new_picking_info = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.return.picking', 'create_returns', [wizard_id]
            )
            new_picking_id = None
            if isinstance(new_picking_info, dict) and 'res_id' in new_picking_info:
                new_picking_id = new_picking_info['res_id']
            elif isinstance(new_picking_info, list) and new_picking_info:
                new_picking_id = new_picking_info[0]
            if not new_picking_id:
                for lot in lots:
                    results[lot] = {'success': False, 'message': "No return picking created"}
                continue

            # ✅ Force picking source to Damage/Stock
            st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.picking', 'write',
                [[new_picking_id], {'location_id': damage_location_id}]
            )

            # Update moves
            moves = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.move', 'search_read',
                [[['picking_id', '=', new_picking_id]]],
                {'fields': ['id', 'product_id']}
            )
            product_move_map = {m['product_id'][0]: m['id'] for m in moves if m.get('product_id')}
            for m in moves:
                pid = m['product_id'][0]
                qty = len(lot_groups.get((po_number, pid), []))
                st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.move', 'write',
                    [[m['id']], {'location_id': damage_location_id, 'product_uom_qty': qty}]
                )

            # Clear existing move lines
            existing_ml = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.move.line', 'search',
                [[['picking_id', '=', new_picking_id]]]
            )
            if existing_ml:
                st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.move.line', 'unlink', [existing_ml]
                )

            # Recreate move lines per lot
            for lot in lots:
                move_line = lot_move_data[lot]
                pid = move_line['product_id'][0]
                move_id = product_move_map.get(pid)
                if not move_id:
                    continue
                st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.move.line', 'create',
                    [{
                        'picking_id': new_picking_id,
                        'move_id': move_id,
                        'product_id': pid,
                        'location_id': damage_location_id,
                        'lot_id': move_line['lot_id'][0],
                        'qty_done': 1,
                    }]
                )

            # ✅ Validate picking (with backorder/immediate wizard handling)
            validate_res = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.picking', 'button_validate', [[new_picking_id]]
            )
            if isinstance(validate_res, dict) and validate_res.get('res_model') == 'stock.immediate.transfer':
                wiz_ids = st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.immediate.transfer', 'search',
                    [[['pick_ids', 'in', [new_picking_id]]]]
                )
                if wiz_ids:
                    st.session_state.models.execute_kw(
                        CONFIG['db'], st.session_state.uid, CONFIG['password'],
                        'stock.immediate.transfer', 'process', [wiz_ids]
                    )
            elif isinstance(validate_res, dict) and validate_res.get('res_model') == 'stock.backorder.confirmation':
                wiz_ids = st.session_state.models.execute_kw(
                    CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.backorder.confirmation', 'search',
                    [[['pick_ids', 'in', [new_picking_id]]]]
                )
                if wiz_ids:
                    st.session_state.models.execute_kw(
                        CONFIG['db'], st.session_state.uid, CONFIG['password'],
                        'stock.backorder.confirmation', 'process', [wiz_ids]
                    )

            # Success
            picking_data = st.session_state.models.execute_kw(
                CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.picking', 'read', [new_picking_id], {'fields': ['name']}
            )
            returned_reference = picking_data[0].get('name', 'N/A') if picking_data else 'N/A'

            for lot in lots:
                results[lot] = {
                    'success': True,
                    'po_number': po_number,
                    'new_picking_id': new_picking_id,
                    'returned_reference': returned_reference,
                    'message': f"Return processed → Picking {returned_reference} (Source=Damage/Stock)"
                }

        except Exception as e:
            for lot in lots:
                results[lot] = {'success': False, 'message': f"Error: {str(e)}"}

    # Summary
    success_count = sum(1 for r in results.values() if r['success'])
    failure_count = len(results) - success_count
    overall_success = success_count > 0
    message = f"Processed {success_count} lots successfully, {failure_count} failed"

    return overall_success, {
        "results": results,
        "success_count": success_count,
        "failure_count": failure_count,
        "message": message
    }

def create_excel_report(non_damaged, damaged, approved, rejected, processed):
    """Create an Excel report with all the inventory data organized by sections"""
    
    # Create a BytesIO object to store the Excel file
    output = io.BytesIO()
    
    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Get the workbook and worksheet objects
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#1f77b4',
            'font_color': 'white',
            'border': 1
        })
        
        summary_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        section_header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'fg_color': '#FFE699',
            'border': 1
        })
        
        # Create a summary sheet
        summary_data = {
            'Category': ['Total Lots Checked', 'Non-Damaged Lots', 'Damaged Lots', 
                         'Approved for Return', 'Rejected for Return', 'Processed Returns'],
            'Count': [
                len(non_damaged) + len(damaged),
                len(non_damaged),
                len(damaged),
                len(approved),
                len(rejected),
                len(processed)
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format the summary sheet
        worksheet = writer.sheets['Summary']
        for col_num, value in enumerate(summary_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-adjust columns width
        for i, col in enumerate(summary_df.columns):
            max_len = max(
                summary_df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.set_column(i, i, max_len)
        
        # Add a chart to the summary sheet
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Inventory Summary',
            'categories': ['Summary', 1, 0, len(summary_data['Category']), 0],
            'values': ['Summary', 1, 1, len(summary_data['Category']), 1],
        })
        chart.set_title({'name': 'Inventory Summary'})
        chart.set_x_axis({'name': 'Category'})
        chart.set_y_axis({'name': 'Count'})
        worksheet.insert_chart('D2', chart)
        
        # Create detailed sheets for each category
        
        # Non-Damaged Items sheet
        if non_damaged:
            non_damaged_data = []
            for item in non_damaged:
                details = item.get('details', {})
                po_details = details.get('po_details', {}) if details else {}
                
                non_damaged_data.append({
                    'lot': item['lot'],
                    'location': item['location'],
                    'status': item['status'],
                    'reference': details.get('reference', 'N/A') if details else 'N/A',
                    'product_name': details.get('product_name', 'N/A') if details else 'N/A',
                    'sku': details.get('sku', 'N/A') if details else 'N/A',
                    'vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                    'price_unit': po_details.get('price_unit', 0) if po_details else 0,
                    'discount': po_details.get('discount', 0) if po_details else 0,
                    'cost_price': po_details.get('cost_price', 0) if po_details else 0
                })
            
            non_damaged_df = pd.DataFrame(non_damaged_data)
            non_damaged_df.to_excel(writer, sheet_name='Non-Damaged Items', index=False)
            worksheet = writer.sheets['Non-Damaged Items']
            for col_num, value in enumerate(non_damaged_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(non_damaged_df.columns):
                max_len = max(
                    non_damaged_df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_len)
        
        # Damaged Items sheet
        if damaged:
            damaged_data = []
            for item in damaged:
                details = item.get('details', {})
                po_details = details.get('po_details', {}) if details else {}
                lot = item['lot']
                
                if lot in processed:
                    status = 'Return Processed'
                elif lot in approved:
                    status = 'Approved for Return'
                elif lot in rejected:
                    status = 'Rejected for Return'
                else:
                    status = 'Pending Action'
                    
                damaged_data.append({
                    'lot': lot,
                    'location': item['location'],
                    'status': status,
                    'reference': details.get('reference', 'N/A') if details else 'N/A',
                    'product_name': details.get('product_name', 'N/A') if details else 'N/A',
                    'sku': details.get('sku', 'N/A') if details else 'N/A',
                    'vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                    'price_unit': po_details.get('price_unit', 0) if po_details else 0,
                    'discount': po_details.get('discount', 0) if po_details else 0,
                    'cost_price': po_details.get('cost_price', 0) if po_details else 0
                })
            
            damaged_df = pd.DataFrame(damaged_data)
            damaged_df.to_excel(writer, sheet_name='Damaged Items', index=False)
            worksheet = writer.sheets['Damaged Items']
            for col_num, value in enumerate(damaged_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(damaged_df.columns):
                max_len = max(
                    damaged_df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_len)
        
        # Processed Returns sheet
        if processed:
            processed_data = []
            for lot, details in processed.items():
                lot_details = st.session_state.lot_details.get(lot, {})
                po_details = lot_details.get('po_details', {}) if lot_details else {}
                
                processed_data.append({
                    'lot': lot,
                    'po_number': details.get('po_number', 'N/A'),
                    'picking_id': details.get('new_picking_id', 'N/A'),
                    'status': 'Return Processed',
                    'timestamp': details.get('timestamp', 'N/A'),
                    'product_name': lot_details.get('product_name', 'N/A') if lot_details else 'N/A',
                    'sku': lot_details.get('sku', 'N/A') if lot_details else 'N/A',
                    'vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                    'reference': lot_details.get('reference', 'N/A') if lot_details else 'N/A',
                    'returned_reference': details.get('returned_reference', 'N/A'),
                    'price_unit': po_details.get('price_unit', 0) if po_details else 0,
                    'discount': po_details.get('discount', 0) if po_details else 0,
                    'cost_price': po_details.get('cost_price', 0) if po_details else 0
                })            

            processed_df = pd.DataFrame(processed_data)
            processed_df.to_excel(writer, sheet_name='Processed Returns', index=False)
            worksheet = writer.sheets['Processed Returns']
            for col_num, value in enumerate(processed_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(processed_df.columns):
                max_len = max(
                    processed_df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_len)
        
        # Approved Lots sheet
        if approved:
            approved_data = []
            for lot in approved:
                lot_details = st.session_state.lot_details.get(lot, {})
                po_details = lot_details.get('po_details', {}) if lot_details else {}
                
                approved_data.append({
                    'lot': lot,
                    'status': 'Approved for Return',
                    'reference': lot_details.get('reference', 'N/A') if lot_details else 'N/A',
                    'product_name': lot_details.get('product_name', 'N/A') if lot_details else 'N/A',
                    'sku': lot_details.get('sku', 'N/A') if lot_details else 'N/A',
                    'vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                    'price_unit': po_details.get('price_unit', 0) if po_details else 0,
                    'discount': po_details.get('discount', 0) if po_details else 0,
                    'cost_price': po_details.get('cost_price', 0) if po_details else 0
                })
            
            approved_df = pd.DataFrame(approved_data)
            approved_df.to_excel(writer, sheet_name='Approved Lots', index=False)
            worksheet = writer.sheets['Approved Lots']
            for col_num, value in enumerate(approved_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(approved_df.columns):
                max_len = max(
                    approved_df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_len)
        
        # Rejected Lots sheet
        if rejected:
            rejected_data = []
            for lot in rejected:
                lot_details = st.session_state.lot_details.get(lot, {})
                po_details = lot_details.get('po_details', {}) if lot_details else {}
                
                rejected_data.append({
                    'lot': lot,
                    'status': 'Rejected for Return',
                    'reference': lot_details.get('reference', 'N/A') if lot_details else 'N/A',
                    'product_name': lot_details.get('product_name', 'N/A') if lot_details else 'N/A',
                    'sku': lot_details.get('sku', 'N/A') if lot_details else 'N/A',
                    'vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                    'price_unit': po_details.get('price_unit', 0) if po_details else 0,
                    'discount': po_details.get('discount', 0) if po_details else 0,
                    'cost_price': po_details.get('cost_price', 0) if po_details else 0
                })
            
            rejected_df = pd.DataFrame(rejected_data)
            rejected_df.to_excel(writer, sheet_name='Rejected Lots', index=False)
            worksheet = writer.sheets['Rejected Lots']
            for col_num, value in enumerate(rejected_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(rejected_df.columns):
                max_len = max(
                    rejected_df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.set_column(i, i, max_len)
    
    # Get the Excel file data
    output.seek(0)
    return output.getvalue()

def create_visualization_charts(non_damaged, damaged, approved, rejected, processed):
    """Create interactive visualization charts for the inventory data"""
    
    # Prepare data for charts
    total_checked = len(non_damaged) + len(damaged)
    
    # Pie chart for inventory status distribution (SMALLER SIZE)
    labels = ['Non-Damaged', 'Damaged - Pending', 'Approved for Return', 'Rejected', 'Processed Returns']
    values = [
        len(non_damaged),
        len([lot for lot in damaged if lot['lot'] not in approved and lot['lot'] not in rejected and lot['lot'] not in processed]),
        len(approved),
        len(rejected),
        len(processed)
    ]
    
    colors = ['#28a745', '#ffc107', '#007bff', '#dc3545', '#6f42c1']
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.4,
        marker_colors=colors,
        textinfo='label+percent+value',
        textfont_size=10,  # Smaller font size
        marker_line=dict(color='#FFFFFF', width=1)  # Thinner border
    )])
    
    fig_pie.update_layout(
        title={
            'text': 'Inventory Status Distribution',
            'x': 0.5,
            'font': {'size': 14, 'color': '#2c3e50'}  # Smaller title
        },
        font=dict(size=10),  # Smaller general font
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=9)  # Smaller legend font
        ),
        height=300,  # Reduced height from 400 to 300
        width=400,   # Added width constraint
        margin=dict(l=20, r=20, t=50, b=20),  # Tighter margins
        annotations=[dict(text='Total<br>Checked<br><b>' + str(total_checked) + '</b>', 
                         x=0.5, y=0.5, font_size=12, showarrow=False)]  # Smaller annotation
    )
    
    # Bar chart for workflow status (ORIGINAL SIZE)
    workflow_data = {
        'Status': ['Total Checked', 'Damaged Items', 'Approved', 'Rejected', 'Processed'],
        'Count': [total_checked, len(damaged), len(approved), len(rejected), len(processed)]
    }
    
    fig_bar = px.bar(
        workflow_data, 
        x='Status', 
        y='Count',
        color='Count',
        color_continuous_scale='viridis',
        title='Inventory Processing Workflow'
    )
    
    fig_bar.update_layout(
        title={
            'x': 0.5,
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title='Processing Status',
        yaxis_title='Number of Items',
        height=400,
        showlegend=False
    )
    
    fig_bar.update_traces(
        texttemplate='%{y}', 
        textposition='outside',
        marker_line_color='rgb(8,48,107)',
        marker_line_width=1.5,
        opacity=0.8
    )
    
    return fig_pie, fig_bar

def display_enhanced_metrics(non_damaged, damaged, approved, rejected, processed):
    """Display enhanced metrics with professional styling"""
    
    total_checked = len(non_damaged) + len(damaged)
    processing_rate = (len(approved) + len(rejected) + len(processed)) / len(damaged) * 100 if damaged else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📊 Total Processed</div>
            <div class="metric-value">{total_checked:,}</div>
            <div style="font-size: 0.8rem; color: #64748b;">Lot/Serial Numbers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⚠️ Damaged Items</div>
            <div class="metric-value">{len(damaged):,}</div>
            <div style="font-size: 0.8rem; color: #dc3545;">Requires Action</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">✅ Processing Rate</div>
            <div class="metric-value">{processing_rate:.1f}%</div>
            <div style="font-size: 0.8rem; color: #28a745;">Items Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        pending_count = len([item for item in damaged if item['lot'] not in approved and 
                            item['lot'] not in rejected and item['lot'] not in processed])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">⏳ Pending Action</div>
            <div class="metric-value">{pending_count:,}</div>
            <div style="font-size: 0.8rem; color: #ffc107;">Awaiting Decision</div>
        </div>
        """, unsafe_allow_html=True)

# Main app layout
st.markdown('<h1 class="main-header fade-in-up">📦 Odoo Inventory Management</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Inventory tracking and returns processing system</p>', unsafe_allow_html=True)

# Enhanced sidebar for authentication and connection
with st.sidebar:
    st.markdown('<h2 class="sidebar-header">🔐 Authentication</h2>', unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.markdown("### Please log in to continue")
        
        # Create a form for login (allows Enter key submission)
        with st.form(key="login_form"):
            username = st.text_input(
                "👤 Username", 
                placeholder="Enter your username", 
                key="username_input",
                autocomplete="username"
            )
            password = st.text_input(
                "🔒 Password", 
                type="password", 
                placeholder="Enter your password", 
                key="password_input",
                autocomplete="current-password"
            )
            
            # Form submit button (responds to Enter key)
            login_submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            # Handle form submission
            if login_submitted:
                if username == CONFIG['app_username'] and password == CONFIG['app_password']:
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        # Add user instruction
        st.caption("💡 Tip: Press Enter after typing your password to login quickly")
        
        
    else:
        st.markdown(f"""
        <div class="status-card success-card">
            <h4>✅ Welcome Back!</h4>
            <p><strong>User:</strong> {CONFIG['app_username']}</p>
            <p><strong>Session:</strong> Active</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
        st.markdown("---")
        st.header("🔗 Related Applications")
            
        # Attractive button links
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
            
        if st.markdown("""
            <a href="https://inventory-debit-note.streamlit.app/" target="_blank">
                <div class="app-button app-button-inventory">
                    <span class="button-icon">📦</span>
                    Inventory Debit Note
                </div>
            </a>
        """, unsafe_allow_html=True):
            pass
    
        if st.markdown("""
            <a href="https://lot-debit-note.streamlit.app/" target="_blank">
                <div class="app-button app-button-lot-debit">
                    <span class="button-icon">🏷️</span>
                    Lot Debit Note
                </div>
            </a>
        """, unsafe_allow_html=True):
            pass
            
        if st.markdown("""
            <a href="https://lot-credit-note.streamlit.app/" target="_blank">
                <div class="app-button app-button-lot-credit">
                    <span class="button-icon">💰</span>
                     Lot Credit Note
                </div>
            </a>
          """, unsafe_allow_html=True):
            pass
    
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<h2 class="sidebar-header">🔗 Odoo Connection</h2>', unsafe_allow_html=True)
        
        if st.session_state.odoo_connected:
            st.markdown("""
            <div class="connection-status connected">
                ✅ Connected to Odoo
                <br><small>System ready for operations</small>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown("""
            <div class="connection-status disconnected">
                ❌ Not Connected to Odoo
                <br><small>Click below to establish connection</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔌 Connect to Odoo", use_container_width=True):
                with st.spinner("🔄 Establishing connection to Odoo..."):
                    success, message = connect_to_odoo()
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

# Main content based on authentication status
if not st.session_state.authenticated:
    # Welcome screen with attractive design
    st.markdown("""
    <div class="welcome-card fade-in-up">
        <h2>🌟 Welcome to Odoo Inventory Management</h2>
        <p>Your comprehensive solution for professional inventory tracking, damage assessment, and returns processing. 
        Built with modern technology to streamline your workflow.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Smart Inventory Check</div>
            <div class="feature-desc">Quickly verify lot/serial numbers across your entire inventory system</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Advanced Analytics</div>
            <div class="feature-desc">Interactive charts and comprehensive reports for data-driven decisions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">🔄</div>
            <div class="feature-title">Automated Returns</div>
            <div class="feature-desc">Streamlined return processing with bulk operations and tracking</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
else:
    if not st.session_state.odoo_connected:
        st.markdown("""
        <div class="status-card warning-card fade-in-up">
            <h3>🔌 Connection Required</h3>
            <p>Please establish a connection to Odoo using the sidebar to access all inventory management features.</p>
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Click "Connect to Odoo" in the sidebar</li>
                <li>Wait for connection confirmation</li>
                <li>Begin your inventory operations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Main inventory management interface
        st.markdown('<h2 class="section-header">🔍 Inventory Status Check</h2>', unsafe_allow_html=True)
        
        # Input methods with enhanced UI
        tab1, tab2 = st.tabs(["📝 Manual Entry", "📄 Excel Upload"])
        
        with tab1:
            st.markdown("### Enter Lot/Serial Numbers")
            st.markdown("*Enter one number per line or separate multiple numbers with commas*")
            
            lot_input = st.text_area(
                "Lot/Serial Numbers",
                height=200,
                placeholder="Example:\nLOT001\nLOT002, LOT003\nSN12345",
                help="You can enter lot numbers one per line or comma-separated on the same line"
            )
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🔍 Check Inventory Status", type="primary", use_container_width=True, key="check_manual"):
                    if lot_input:
                        # Parse input (support both comma-separated and newline-separated)
                        lot_serials = []
                        for line in lot_input.split('\n'):
                            if ',' in line:
                                lot_serials.extend([ls.strip() for ls in line.split(',') if ls.strip()])
                            else:
                                if line.strip():
                                    lot_serials.append(line.strip())
                        
                        if lot_serials:
                            with st.spinner("🔍 Analyzing inventory status..."):
                                non_damaged, damaged = check_inventory(lot_serials)
                                st.session_state.inventory_results = {
                                    'non_damaged': non_damaged,
                                    'damaged': damaged
                                }
                                st.session_state.damaged_lots = [item['lot'] for item in damaged]
                                
                                # Get PO numbers for damaged lots
                                st.session_state.lot_po_mapping = {}
                                for item in damaged:
                                    lot = item['lot']
                                    po_number = get_po_for_lot(lot)
                                    st.session_state.lot_po_mapping[lot] = po_number
                                    
                            st.success(f"✅ Successfully processed {len(lot_serials)} lot numbers!")
                            st.rerun()
                        else:
                            st.error("Please enter at least one valid lot/serial number")
                    else:
                        st.error("Please enter some lot/serial numbers")
            
            with col2:
                if st.button("🧹 Clear", use_container_width=True):
                    st.rerun()
        
        with tab2:
            st.markdown("### Upload Excel File")
            st.markdown("*Supported formats: .xlsx, .xls*")
            
            uploaded_file = st.file_uploader(
                "Choose an Excel file",
                type=['xlsx', 'xls'],
                help="The Excel file should contain a column with 'Lot' or 'Serial' in the name"
            )
            
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    # Check for different possible column names
                    lot_column = None
                    for col in df.columns:
                        if 'lot' in col.lower() or 'serial' in col.lower():
                            lot_column = col
                            break
                    
                    if lot_column:
                        lot_serials = df[lot_column].dropna().astype(str).tolist()
                        st.success(f"📄 Found **{len(lot_serials)}** lot numbers in column: **{lot_column}**")
                        
                        # Show preview
                        with st.expander("📋 Preview Data"):
                            st.dataframe(df.head(10), use_container_width=True)
                        
                        if st.button("🔍 Check Inventory Status", type="primary", key="check_file"):
                            with st.spinner("🔍 Processing Excel file data..."):
                                non_damaged, damaged = check_inventory(lot_serials)
                                st.session_state.inventory_results = {
                                    'non_damaged': non_damaged,
                                    'damaged': damaged
                                }
                                st.session_state.damaged_lots = [item['lot'] for item in damaged]
                                
                                # Get PO numbers for damaged lots
                                st.session_state.lot_po_mapping = {}
                                for item in damaged:
                                    lot = item['lot']
                                    po_number = get_po_for_lot(lot)
                                    st.session_state.lot_po_mapping[lot] = po_number
                                    
                            st.success(f"✅ Successfully processed {len(lot_serials)} lot numbers from Excel!")
                            st.rerun()
                    else:
                        st.error("❌ Excel file must contain a column with 'Lot' or 'Serial' in the name")
                except Exception as e:
                    st.error(f"❌ Error reading Excel file: {str(e)}")
        
        # Display results if available
        if st.session_state.inventory_results is not None:
            if isinstance(st.session_state.inventory_results, dict) and 'non_damaged' in st.session_state.inventory_results:
                non_damaged = st.session_state.inventory_results['non_damaged']
                damaged = st.session_state.inventory_results['damaged']
                
                st.markdown("---")
                st.markdown('<h2 class="section-header">📊 Analysis Results</h2>', unsafe_allow_html=True)
                
                # Enhanced metrics display
                display_enhanced_metrics(non_damaged, damaged, st.session_state.approved_lots, 
                                       st.session_state.rejected_lots, st.session_state.processed_lots)
                
                # Interactive visualizations
                if non_damaged or damaged:
                    st.markdown('<h3 class="section-header">📈 Visual Analytics</h3>', unsafe_allow_html=True)
                    
                    fig_pie, fig_bar = create_visualization_charts(
                        non_damaged, damaged, st.session_state.approved_lots,
                        st.session_state.rejected_lots, st.session_state.processed_lots
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_bar, use_container_width=True)
                
                # Display detailed results
                if non_damaged:
                    st.markdown('<h3 class="section-header">✅ Non-Damaged Items</h3>', unsafe_allow_html=True)
                    st.markdown(f"**{len(non_damaged)}** items are not in damage stock")
                    
                    with st.expander("🔍 View Details", expanded=True):
                        non_damaged_data = []
                        for item in non_damaged:
                            details = item.get('details', {})
                            po_details = details.get('po_details', {}) if details else {}

                            non_damaged_data.append({
                                'Lot/Serial': item['lot'],
                                'Location': item['location'],
                                'Status': item['status'],
                                'Reference': details.get('reference', 'N/A') if details else 'N/A',
                                'Product': details.get('product_name', 'N/A') if details else 'N/A',
                                'SKU': details.get('sku', 'N/A') if details else 'N/A',
                                'Vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                                'Price': f"${po_details.get('price_unit', 0):.2f}",
                                'Discount': f"{po_details.get('discount', 0)}%" if po_details.get('discount', 0) else "0%",
                                'Cost Price': f"${po_details.get('cost_price', 0):.2f}",
                            })

                        non_damaged_df = pd.DataFrame(non_damaged_data)
                        st.dataframe(non_damaged_df, use_container_width=True, height=300)

                
                # Enhanced damaged items section
                if damaged:
                    st.markdown('<h3 class="section-header">⚠️ Damaged Items Management</h3>', unsafe_allow_html=True)
                    
                    # Create enhanced damaged items table
                    damaged_data = []
                    for item in damaged:
                        lot = item['lot']
                        po_number = st.session_state.lot_po_mapping.get(lot, "Not Found")
                        details = item.get('details', {})
                        po_details = details.get('po_details', {}) if details else {}

                        if lot in st.session_state.processed_lots:
                            status = '✅ Return Processed'
                        elif lot in st.session_state.approved_lots:
                            status = '📝 Approved for Return'
                        elif lot in st.session_state.rejected_lots:
                            status = '❌ Rejected for Return'
                        else:
                            status = '⏳ Pending Action'

                        damaged_data.append({
                            'Lot/Serial': lot,
                            'Location': item['location'],
                            'PO Number': po_number,
                            'Status': status,
                            'Reference': details.get('reference', 'N/A') if details else 'N/A',
                            'Product': details.get('product_name', 'N/A') if details else 'N/A',
                            'SKU': details.get('sku', 'N/A') if details else 'N/A',
                            'Vendor': po_details.get('vendor', 'N/A') if po_details else 'N/A',
                            'Price': f"${po_details.get('price_unit', 0):.2f}",
                            'Discount': f"{po_details.get('discount', 0)}%" if po_details.get('discount', 0) else "0%",
                            'Cost Price': f"${po_details.get('cost_price', 0):.2f}",
                        })

                    damaged_df = pd.DataFrame(damaged_data)
                    st.dataframe(damaged_df, use_container_width=True, height=400)
                    
                    # Bulk action management
                    st.markdown('<div class="action-panel">', unsafe_allow_html=True)
                    st.markdown('<div class="action-title">🎯 Bulk Actions</div>', unsafe_allow_html=True)
                    
                    # Get lots that are pending action
                    pending_lots = [item['lot'] for item in damaged if item['lot'] not in st.session_state.processed_lots and 
                                   item['lot'] not in st.session_state.approved_lots and 
                                   item['lot'] not in st.session_state.rejected_lots]
                    
                    if pending_lots:
                        st.markdown(f"**{len(pending_lots)}** items are awaiting your decision")
                        
                        # Selection controls
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            # Select all checkbox with proper session state handling
                            if "select_all_damaged" not in st.session_state:
                                st.session_state.select_all_damaged = False

                            # Handle select all logic
                            select_all = st.checkbox(
                                f"🔘 Select All ({len(pending_lots)} items)", 
                                value=st.session_state.select_all_damaged,
                                key="select_all_damaged_checkbox"
                            )

                            # Update session state when checkbox changes
                            if select_all != st.session_state.select_all_damaged:
                                st.session_state.select_all_damaged = select_all
                                if select_all:
                                    st.session_state.selected_damaged_lots = pending_lots.copy()
                                else:
                                    st.session_state.selected_damaged_lots = []
                                st.rerun()

                            # Apply select all state to the multiselect
                            if st.session_state.select_all_damaged:
                                default_selection = pending_lots
                            else:
                                default_selection = st.session_state.selected_damaged_lots

                        with col2:
                            st.markdown(f"**Selected:** {len(st.session_state.selected_damaged_lots)}")

                        # Multi-select for specific items
                        selected_lots = st.multiselect(
                            "🎯 Select specific lots for action:",
                            options=pending_lots,
                            default=default_selection,
                            key="damaged_lots_select",
                            help="Choose individual items or use 'Select All' above"
                        )

                        # Update session state when selection changes
                        if selected_lots != st.session_state.selected_damaged_lots:
                            st.session_state.selected_damaged_lots = selected_lots
                            # If all items are selected, check the select all box
                            if set(selected_lots) == set(pending_lots) and pending_lots:
                                st.session_state.select_all_damaged = True
                            elif st.session_state.select_all_damaged:
                                st.session_state.select_all_damaged = False
                            st.rerun()

                        
                        if st.session_state.selected_damaged_lots:
                            st.info(f"💡 {len(st.session_state.selected_damaged_lots)} item(s) selected for action")
                            
                            # Action buttons with enhanced styling
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button(
                                    f"✅ Approve Selected ({len(st.session_state.selected_damaged_lots)})",
                                    type="primary", 
                                    use_container_width=True
                                ):
                                    for lot in st.session_state.selected_damaged_lots:
                                        if lot not in st.session_state.approved_lots:
                                            st.session_state.approved_lots.append(lot)
                                        if lot in st.session_state.rejected_lots:
                                            st.session_state.rejected_lots.remove(lot)
                                    
                                    st.success(f"✅ Approved {len(st.session_state.selected_damaged_lots)} items for return!")
                                    st.session_state.selected_damaged_lots = []
                                    time.sleep(1)
                                    st.rerun()
                            
                            with col2:
                                if st.button(
                                    f"❌ Reject Selected ({len(st.session_state.selected_damaged_lots)})",
                                    use_container_width=True
                                ):
                                    for lot in st.session_state.selected_damaged_lots:
                                        if lot not in st.session_state.rejected_lots:
                                            st.session_state.rejected_lots.append(lot)
                                        if lot in st.session_state.approved_lots:
                                            st.session_state.approved_lots.remove(lot)
                                    
                                    st.warning(f"❌ Rejected {len(st.session_state.selected_damaged_lots)} items!")
                                    st.session_state.selected_damaged_lots = []
                                    time.sleep(1)
                                    st.rerun()
                            
                            with col3:
                                if st.button("🔄 Clear Selection", use_container_width=True):
                                    st.session_state.selected_damaged_lots = []
                                    st.session_state.select_all_damaged = False
                                    st.rerun()
                    else:
                        st.success("🎉 All damaged items have been processed!")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Process approved returns section
                    if st.session_state.approved_lots:
                        st.markdown("---")
                        st.markdown('<h3 class="section-header">🔄 Return Processing Center</h3>', unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="status-card info-card">
                            <h4>📋 Ready for Processing</h4>
                            <p><strong>{len(st.session_state.approved_lots)}</strong> lot(s) have been approved and are ready for return processing.</p>
                            <p><strong>Next Step:</strong> Click the button below to process all approved returns.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show approved items
                        with st.expander("📋 View Approved Items", expanded=False):
                            approved_data = []
                            for lot in st.session_state.approved_lots:
                                po_number = st.session_state.lot_po_mapping.get(lot, "Not Found")
                                approved_data.append({
                                    'Lot/Serial': lot,
                                    'PO Number': po_number,
                                    'Status': 'Approved for Return'
                                })
                            
                            approved_df = pd.DataFrame(approved_data)
                            st.dataframe(approved_df, use_container_width=True)
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            if st.button(
                                f"🚀 Process Returns for All Approved Lots ({len(st.session_state.approved_lots)})",
                                type="primary",
                                use_container_width=True
                            ):
                                with st.spinner("🔄 Processing returns... This may take a moment."):
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    success, result = process_product_return(st.session_state.approved_lots)
                                    
                                    if success:
                                        # Update processed lots with individual results
                                        processed_count = 0
                                        for lot in st.session_state.approved_lots:
                                            if lot in result['results'] and result['results'][lot]['success']:
                                                # This is the correct way to add to a dictionary
                                                st.session_state.processed_lots[lot] = {
                                                    'status': 'Return Processed',
                                                    'po_number': result['results'][lot].get('po_number', 'N/A'),
                                                    'new_picking_id': result['results'][lot].get('new_picking_id', 'N/A'),
                                                    'returned_reference': result['results'][lot].get('returned_reference', 'N/A'),
                                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                }
                                                processed_count += 1
                                        
                                        # Clear approved lots
                                        st.session_state.approved_lots = []
                                        
                                        # Show detailed results
                                        st.markdown(f"""
                                        <div class="status-card success-card">
                                            <h4>🎉 Processing Complete!</h4>
                                            <p><strong>✅ Successful:</strong> {result['success_count']} returns processed</p>
                                            <p><strong>❌ Failed:</strong> {result['failure_count']} returns failed</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if result['failure_count'] > 0:
                                            with st.expander("❌ View Failed Returns"):
                                                for lot, res in result['results'].items():
                                                    if not res['success']:
                                                        st.error(f"**{lot}:** {res['message']}")
                                        
                                        progress_bar.empty()
                                        status_text.empty()
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Return processing failed: {result}")
                                        progress_bar.empty()
                                        status_text.empty()
                        
                        with col2:
                            if st.button("📋 View Details", use_container_width=True):
                                # This could expand to show more details
                                pass
                
                # Summary section with processed items
                if st.session_state.processed_lots:
                    st.markdown('<h3 class="section-header">✅ Processed Returns Summary</h3>', unsafe_allow_html=True)
                    
                    processed_data = []
                    for lot, details in st.session_state.processed_lots.items():
                        processed_data.append({
                            'Lot/Serial': lot,
                            'PO Number': details.get('po_number', 'N/A'),
                            'Returned Reference': details.get('returned_reference', 'N/A'),  # ✅ Added
                            'Picking ID': details.get('new_picking_id', 'N/A'),
                            'Status': '✅ Completed',
                            'Processed Time': details.get('timestamp', 'N/A')
                        })
                    
                    processed_df = pd.DataFrame(processed_data)
                    
                    with st.expander(f"📋 View Processed Returns ({len(processed_data)} items)", expanded=False):
                        st.dataframe(processed_df, use_container_width=True)

                
                # Enhanced report download section
                st.markdown("---")
                st.markdown('<h3 class="section-header">📊 Comprehensive Reports</h3>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)  # Adds a line break for spacing
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Create Excel report
                    excel_data = create_excel_report(
                        non_damaged, 
                        damaged, 
                        st.session_state.approved_lots,
                        st.session_state.rejected_lots,
                        st.session_state.processed_lots
                    )
                    
                    # Enhanced download button
                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=create_excel_report(
                            non_damaged, damaged,
                            st.session_state.approved_lots,
                            st.session_state.rejected_lots,
                            st.session_state.processed_lots
                        ),
                        file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📊 Report Contents</div>
                        <div style="font-size: 0.9rem; color: #64748b;">
                            • Summary Dashboard<br>
                            • Non-Damaged Items<br>
                            • Damaged Items<br>
                            • Approved Lots<br>
                            • Rejected Lots<br>
                            • Processed Returns<br>
                            • Interactive Charts
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Quick actions panel
                st.markdown('<div class="action-panel">', unsafe_allow_html=True)
                st.markdown('<div class="action-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 New Analysis", use_container_width=True):
                        # Clear current results
                        st.session_state.inventory_results = None
                        st.session_state.damaged_lots = []
                        st.session_state.selected_damaged_lots = []
                        st.session_state.lot_po_mapping = {}
                        st.rerun()
                
                with col2:
                    if st.button("🧹 Reset All Data", use_container_width=True):
                        # Clear all session data except authentication
                        keys_to_clear = ['inventory_results', 'damaged_lots', 'approved_lots', 
                                    'rejected_lots', 'processed_lots', 'selected_damaged_lots', 
                                    'lot_po_mapping']
                        for key in keys_to_clear:
                            if key in st.session_state:
                                if key == 'processed_lots':
                                    st.session_state[key] = {}  # Reset to empty dictionary
                                elif 'lots' in key:
                                    st.session_state[key] = []  # Reset to empty list
                                else:
                                    st.session_state[key] = None
                        st.success("🧹 All data cleared successfully!")
                        time.sleep(1)
                        st.rerun()
                
                with col3:
                    if st.button("📊 View Analytics", use_container_width=True):
                        # Scroll to analytics section (this is more of a placeholder)
                        st.info("📈 Analytics are displayed above in the Visual Analytics section")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                st.error("❌ Inventory results are in an unexpected format. Please check the inventory again.")

# Enhanced footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <div class="footer-content">
        <strong>📦 Odoo Inventory Management System</strong> • Powered by Streamlit
    </div>
    <div class="footer-sub">
        Professional inventory tracking • Advanced analytics • Streamlined workflow
    </div>
</div>
""", unsafe_allow_html=True)
