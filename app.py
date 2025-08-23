import streamlit as st
import xmlrpc.client
import os
from dotenv import load_dotenv
import pandas as pd
import time
from datetime import datetime
import io

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

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin-bottom: 20px;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
        margin-bottom: 20px;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
    }
    .stButton>button:hover {
        background-color: #0d5d99;
        color: white;
    }
    .connection-status {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    .connected {
        background-color: #d4edda;
        color: #155724;
    }
    .disconnected {
        background-color: #f8d7da;
        color: #721c24;
    }
    .damaged-table {
        margin-bottom: 20px;
    }
    .non-damaged-table {
        margin-bottom: 20px;
    }
    .action-buttons {
        display: flex;
        gap: 10px;
        margin: 20px 0;
    }
    .approve-btn {
        background-color: #28a745 !important;
    }
    .reject-btn {
        background-color: #dc3545 !important;
    }
    .select-all-checkbox {
        margin-bottom: 10px;
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
    st.session_state.processed_lots = {}
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None
if 'selected_damaged_lots' not in st.session_state:
    st.session_state.selected_damaged_lots = []
if 'select_all_damaged' not in st.session_state:
    st.session_state.select_all_damaged = False
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

def check_inventory(lot_serials):
    """Check if lot/serial numbers are in damage stock"""
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
        
        quant_records = st.session_state.models.execute_kw(
            CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.quant', 'search_read',
            [[('lot_id.name', '=', lot)]],
            {'fields': ['lot_id', 'location_id']}
        )

        if quant_records:
            found_in_damage = any(q['location_id'][1] == CONFIG['damage_location_name'] for q in quant_records)
            if not found_in_damage:
                # Get all locations for this lot
                locations = {q['location_id'][1] for q in quant_records if q['location_id']}
                not_in_damage_stock.append({
                    'lot': lot, 
                    'location': ", ".join(locations) if locations else "Unknown",
                    'status': 'Not in Damage'
                })
            else:
                in_damage_stock.append({
                    'lot': lot,
                    'location': CONFIG['damage_location_name'],
                    'status': 'In Damage'
                })
        else:
            not_in_damage_stock.append({
                'lot': lot, 
                'location': "Not Found in stock.quant",
                'status': 'Not Found'
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
    """Process product return for given lot/serial numbers with individual PO handling"""
    unique_lots = list(set(lot_serials))  # Ensure no duplicates

    if not unique_lots:
        return False, "No Lot/Serial numbers entered."

    # Fetch Company ID
    company_id = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
        'res.company', 'search_read',
        [[['name', '=', CONFIG['hq_company_name']]]],
        {'fields': ['id'], 'limit': 1})[0]['id']

    # Find Damage/Stock Location
    damage_location = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
        'stock.location', 'search_read',
        [[['complete_name', 'ilike', 'Damge/Stock'], ['company_id', '=', company_id]]],
        {'fields': ['id'], 'limit': 1})
    if not damage_location:
        return False, "Damage/Stock location not found"
    damage_location_id = damage_location[0]['id']

    # Group lots by PO
    po_lot_map = {}
    for lot in unique_lots:
        po_number = get_po_for_lot(lot)
        if po_number not in po_lot_map:
            po_lot_map[po_number] = []
        po_lot_map[po_number].append(lot)
    
    # Process returns for each PO group
    results = {}
    for po_number, lots in po_lot_map.items():
        if po_number.startswith("Error:") or po_number == "Not Found":
            # Skip lots with no PO or error
            for lot in lots:
                results[lot] = {
                    'success': False,
                    'message': f"Cannot process return: {po_number}"
                }
            continue
            
        # Find Pickings linked to these Lots for this PO
        lot_quants = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.quant', 'search_read',
            [[
                ['company_id', '=', company_id],
                ['lot_id.name', 'in', lots]
            ]],
            {'fields': ['id', 'lot_id', 'product_id', 'location_id']})

        if not lot_quants:
            for lot in lots:
                results[lot] = {
                    'success': False,
                    'message': f"No stock quants found for lot: {lot}"
                }
            continue

        # Find picking for this PO
        picking_records = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.picking', 'search_read',
            [[['origin', '=', po_number]]],
            {'fields': ['id'], 'limit': 1})
            
        if not picking_records:
            for lot in lots:
                results[lot] = {
                    'success': False,
                    'message': f"No picking found for PO: {po_number}"
                }
            continue
            
        picking_id = picking_records[0]['id']

        # Create Return Wizard
        wizard_id = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.return.picking', 'create', [{'picking_id': picking_id}])

        # Get Return Lines (wizard)
        return_lines = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.return.picking.line', 'search_read',
            [[['wizard_id', '=', wizard_id]]],
            {'fields': ['id', 'product_id', 'quantity', 'move_id']})

        # Map Input Lots -> Product using move lines of original picking
        move_lines = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.move.line', 'search_read',
            [[['picking_id', '=', picking_id], ['lot_id.name', 'in', lots]]],
            {'fields': ['id', 'product_id', 'lot_id', 'qty_done']})

        product_lot_map = {}
        lot_quant_map = {}
        for ml in move_lines:
            if ml['lot_id'] and ml['product_id']:
                pid = ml['product_id'][0]
                lot_name = ml['lot_id'][1]
                product_lot_map.setdefault(pid, []).append(lot_name)
                lot_quant_map[lot_name] = ml

        # Update wizard line quantities
        for line in return_lines:
            product_id = line['product_id'][0]
            qty = len(product_lot_map.get(product_id, []))
            st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.return.picking.line', 'write',
                [[line['id']], {'quantity': qty}])

        # Confirm Return
        new_picking_info = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.return.picking', 'create_returns', [wizard_id])

        new_picking_id = None
        if isinstance(new_picking_info, dict) and 'res_id' in new_picking_info:
            new_picking_id = new_picking_info['res_id']
        elif isinstance(new_picking_info, list) and len(new_picking_info) > 0:
            new_picking_id = new_picking_info[0]
        if not new_picking_id:
            for lot in lots:
                results[lot] = {
                    'success': False,
                    'message': "Could not retrieve the new return picking ID."
                }
            continue

        # Set Picking Source to Damage/Stock
        st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.picking', 'write',
            [[new_picking_id], {'location_id': damage_location_id}])

        # Update moves with demand
        moves = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.move', 'search_read',
            [[['picking_id', '=', new_picking_id]]],
            {'fields': ['id', 'product_id', 'product_uom_qty']})

        product_move_map = {m['product_id'][0]: m['id'] for m in moves if m.get('product_id')}

        for m in moves:
            pid = m['product_id'][0]
            qty = len(product_lot_map.get(pid, []))
            st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.move', 'write',
                [[m['id']], {'location_id': damage_location_id, 'product_uom_qty': qty}])

        # Clear existing move lines
        existing_ml = st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
            'stock.move.line', 'search',
            [[['picking_id', '=', new_picking_id]]])
        if existing_ml:
            st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
                'stock.move.line', 'unlink', [existing_ml])

        # Create new move lines per lot
        for lot in lots:
            ml = lot_quant_map.get(lot)
            if not ml:
                results[lot] = {
                    'success': False,
                    'message': f"No move line found for lot: {lot}"
                }
                continue
                
            pid = ml['product_id'][0]
            move_id = product_move_map.get(pid)
            if not move_id:
                results[lot] = {
                    'success': False,
                    'message': f"No move found for product ID: {pid}"
                }
                continue
                
            try:
                st.session_state.models.execute_kw(CONFIG['db'], st.session_state.uid, CONFIG['password'],
                    'stock.move.line', 'create',
                    [{
                        'picking_id': new_picking_id,
                        'move_id': move_id,
                        'product_id': pid,
                        'location_id': damage_location_id,
                        'lot_id': ml['lot_id'][0],
                        'qty_done': 1,
                    }])
                
                results[lot] = {
                    'success': True,
                    'po_number': po_number,
                    'new_picking_id': new_picking_id,
                    'message': "Return successfully processed"
                }
            except Exception as e:
                results[lot] = {
                    'success': False,
                    'message': f"Error creating move line: {str(e)}"
                }

    # Count successes and failures
    success_count = sum(1 for r in results.values() if r['success'])
    failure_count = len(results) - success_count
    
    # Prepare overall result
    overall_success = success_count > 0
    message = f"Processed {success_count} lots successfully, {failure_count} failed"
    
    return overall_success, {
        "results": results,
        "success_count": success_count,
        "failure_count": failure_count,
        "message": message
    }

def create_excel_report(non_damaged, damaged, approved, rejected, processed):
    """Create an Excel report with all the inventory data"""
    
    # Create DataFrames for each category
    non_damaged_df = pd.DataFrame(non_damaged)
    damaged_df = pd.DataFrame(damaged)
    
    # Create approved/rejected DataFrames
    approved_df = pd.DataFrame([{'lot': lot, 'status': 'Approved for Return'} for lot in approved])
    rejected_df = pd.DataFrame([{'lot': lot, 'status': 'Rejected for Return'} for lot in rejected])
    
    # Create processed DataFrames
    processed_data = []
    for lot, details in processed.items():
        processed_data.append({
            'lot': lot,
            'status': 'Return Processed',
            'po_number': details.get('po_number', 'N/A'),
            'picking_id': details.get('new_picking_id', 'N/A')
        })
    processed_df = pd.DataFrame(processed_data)
    
    # Combine all data
    all_data = pd.concat([non_damaged_df, damaged_df, approved_df, rejected_df, processed_df], ignore_index=True)
    
    return all_data

# Main app layout
st.markdown('<h1 class="main-header">📦 Odoo Inventory Management</h1>', unsafe_allow_html=True)

# Sidebar for authentication and connection
with st.sidebar:
    st.header("🔐 Authentication")
    
    if not st.session_state.authenticated:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username == CONFIG['app_username'] and password == CONFIG['app_password']:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.success(f"Logged in as {CONFIG['app_username']}")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.odoo_connected = False
            st.session_state.uid = None
            st.session_state.models = None
            st.session_state.inventory_results = None
            st.session_state.damaged_lots = []
            st.session_state.approved_lots = []
            st.session_state.rejected_lots = []
            st.session_state.processed_lots = {}
            st.session_state.selected_damaged_lots = []
            st.session_state.lot_po_mapping = {}
            st.rerun()
        
        st.markdown("---")
        st.header("🔗 Odoo Connection")
        
        if st.session_state.odoo_connected:
            st.markdown('<div class="connection-status connected">✅ Connected to Odoo</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="connection-status disconnected">❌ Not Connected to Odoo</div>', unsafe_allow_html=True)
            
            if st.button("Connect to Odoo"):
                with st.spinner("Connecting to Odoo..."):
                    success, message = connect_to_odoo()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# Main content based on authentication status
if not st.session_state.authenticated:
    st.markdown("""
    <div class="info-box">
        <h3>Welcome to Odoo Inventory Management</h3>
        <p>Please log in using the sidebar to access the inventory management features.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    if not st.session_state.odoo_connected:
        st.markdown("""
        <div class="warning-box">
            <h3>Connection Required</h3>
            <p>Please connect to Odoo using the sidebar to proceed with inventory operations.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<h2 class="sub-header">Inventory Status Check</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Option 1: Manual Entry")
            lot_input = st.text_area("Enter Lot/Serial numbers (one per line or comma-separated)", height=150)
            if st.button("Check Inventory Status", key="check_manual"):
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
                        with st.spinner("Checking inventory status..."):
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
                    else:
                        st.error("Please enter at least one valid lot/serial number")
                else:
                    st.error("Please enter some lot/serial numbers")
        
        with col2:
            st.markdown("### Option 2: Upload Excel File")
            uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
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
                        st.success(f"Found {len(lot_serials)} lot numbers in the file")
                        
                        if st.button("Check Inventory Status", key="check_file"):
                            with st.spinner("Checking inventory status..."):
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
                    else:
                        st.error("Excel file must contain a column with 'Lot' or 'Serial' in the name")
                except Exception as e:
                    st.error(f"Error reading Excel file: {str(e)}")
        
        # Display results if available
        if st.session_state.inventory_results is not None:
            # Check if inventory_results is a dictionary with the expected keys
            if isinstance(st.session_state.inventory_results, dict) and 'non_damaged' in st.session_state.inventory_results and 'damaged' in st.session_state.inventory_results:
                non_damaged = st.session_state.inventory_results['non_damaged']
                damaged = st.session_state.inventory_results['damaged']
                
                st.markdown("---")
                st.markdown("### 📊 Inventory Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Lots Checked", len(non_damaged) + len(damaged))
                    st.metric("Non-Damaged Lots", len(non_damaged))
                
                with col2:
                    st.metric("Damaged Lots", len(damaged))
                    st.metric("Damaged Lots Pending Action", len([lot for lot in st.session_state.damaged_lots if lot not in st.session_state.processed_lots and lot not in st.session_state.rejected_lots]))
                
                # Display non-damaged items in a table
                if non_damaged:
                    st.markdown("---")
                    st.markdown("### ✅ Non-Damaged Items")
                    non_damaged_df = pd.DataFrame(non_damaged)
                    st.dataframe(non_damaged_df, use_container_width=True)
                
                # Display damaged items with bulk actions
                if damaged:
                    st.markdown("---")
                    st.markdown("### ⚠️ Damaged Items - Action Required")
                    
                    # Create a DataFrame for damaged items with PO information
                    damaged_data = []
                    for item in damaged:
                        lot = item['lot']
                        po_number = st.session_state.lot_po_mapping.get(lot, "Not Found")
                        
                        if lot in st.session_state.processed_lots:
                            status = 'Return Processed'
                        elif lot in st.session_state.approved_lots:
                            status = 'Approved for Return'
                        elif lot in st.session_state.rejected_lots:
                            status = 'Rejected for Return'
                        else:
                            status = 'Pending Action'
                            
                        damaged_data.append({
                            'lot': lot,
                            'location': item['location'],
                            'po_number': po_number,
                            'action_status': status
                        })
                    
                    damaged_df = pd.DataFrame(damaged_data)
                    
                    # Display the damaged items table
                    st.dataframe(damaged_df, use_container_width=True)
                    
                    # Bulk action section
                    st.markdown("### Bulk Actions for Damaged Items")
                    
                    # Get lots that are pending action
                    pending_lots = [item['lot'] for item in damaged if item['lot'] not in st.session_state.processed_lots and 
                                   item['lot'] not in st.session_state.approved_lots and 
                                   item['lot'] not in st.session_state.rejected_lots]
                    
                    if pending_lots:
                        # Select all checkbox
                        select_all = st.checkbox("Select All Pending Items", value=st.session_state.select_all_damaged, key="select_all_damaged")

                        if select_all:
                            st.session_state.selected_damaged_lots = pending_lots.copy()
                        else:
                            st.session_state.selected_damaged_lots = []

                        
                        # Multi-select for specific items
                        selected_lots = st.multiselect(
                            "Select specific lots for action:",
                            options=pending_lots,
                            default=st.session_state.selected_damaged_lots,
                            key="damaged_lots_select"
                        )
                        
                        st.session_state.selected_damaged_lots = selected_lots
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Approve Selected for Return", type="primary", use_container_width=True):
                                for lot in st.session_state.selected_damaged_lots:
                                    if lot not in st.session_state.approved_lots:
                                        st.session_state.approved_lots.append(lot)
                                    if lot in st.session_state.rejected_lots:
                                        st.session_state.rejected_lots.remove(lot)
                                st.session_state.selected_damaged_lots = []
                                st.rerun()
                        
                        with col2:
                            if st.button("Reject Selected", type="secondary", use_container_width=True):
                                for lot in st.session_state.selected_damaged_lots:
                                    if lot not in st.session_state.rejected_lots:
                                        st.session_state.rejected_lots.append(lot)
                                    if lot in st.session_state.approved_lots:
                                        st.session_state.approved_lots.remove(lot)
                                st.session_state.selected_damaged_lots = []
                                st.rerun()
                    
                    # Process approved returns
                    if st.session_state.approved_lots:
                        st.markdown("---")
                        st.markdown("### 🔄 Process Approved Returns")
                        st.info(f"{len(st.session_state.approved_lots)} lots approved for return processing")
                        
                        if st.button("Process Returns for All Approved Lots", type="primary"):
                            with st.spinner("Processing returns..."):
                                success, result = process_product_return(st.session_state.approved_lots)
                                
                                if success:
                                    # Update processed lots with individual results
                                    for lot in st.session_state.approved_lots:
                                        if lot in result['results'] and result['results'][lot]['success']:
                                            st.session_state.processed_lots[lot] = {
                                                'status': 'Return Processed',
                                                'po_number': result['results'][lot].get('po_number', 'N/A'),
                                                'new_picking_id': result['results'][lot].get('new_picking_id', 'N/A'),
                                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                    
                                    # Clear approved lots
                                    st.session_state.approved_lots = []
                                    
                                    st.success(f"Returns processed: {result['success_count']} successful, {result['failure_count']} failed")
                                    if result['failure_count'] > 0:
                                        st.warning("Some returns failed. Check the details below.")
                                        for lot, res in result['results'].items():
                                            if not res['success']:
                                                st.error(f"Lot {lot}: {res['message']}")
                                    st.rerun()
                                else:
                                    st.error(f"Return processing failed: {result}")
                
                # Create and download Excel report
                st.markdown("---")
                st.markdown("### 📊 Download Report")
                
                # Prepare data for Excel report
                excel_data = create_excel_report(
                    non_damaged, 
                    damaged, 
                    st.session_state.approved_lots,
                    st.session_state.rejected_lots,
                    st.session_state.processed_lots
                )
                
                # Convert DataFrame to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    excel_data.to_excel(writer, sheet_name='Inventory Report', index=False)
                    
                    # Get the workbook and worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Inventory Report']
                    
                    # Add formats
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#1f77b4',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    # Write the column headers with the defined format
                    for col_num, value in enumerate(excel_data.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust columns width
                    for i, col in enumerate(excel_data.columns):
                        max_len = max(
                            excel_data[col].astype(str).map(len).max(),
                            len(col)
                        ) + 2
                        worksheet.set_column(i, i, max_len)
                
                # Create download button
                st.download_button(
                    label="Download Excel Report",
                    data=output.getvalue(),
                    file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Inventory results are in an unexpected format. Please check the inventory again.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6c757d; padding-top: 20px;">
        <p>Odoo Inventory Management • Powered by Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
