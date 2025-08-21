import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QToolBar,
    QFileDialog, QMessageBox, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QRadioButton, QButtonGroup, QTreeWidget, QTreeWidgetItem, QDialog, QGroupBox, QListWidget,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, 
    QLabel, QLineEdit, QComboBox, QTextEdit, QProgressBar, QTreeWidget, QTreeWidgetItem, QDialog, QFormLayout, 
    QSpinBox, QDoubleSpinBox, QDialogButtonBox, QCheckBox, QDateEdit, QSizePolicy, QGridLayout , QSpacerItem, QMenu
)
from PyQt6.QtGui import QIcon, QAction, QPalette, QColor, QPixmap, QFont
from PyQt6.QtCore import Qt, QDate, QTimer
import mysql.connector
from mysql.connector import Error
import logging
import datetime
import json
import shutil
import subprocess
import glob
import os
from datetime import datetime, date
from fpdf import FPDF
import hashlib
from collections import defaultdict
import calendar
import traceback
from mysql.connector.locales.eng import client_error

#Set TEST Environment
TEST_FLAG=True
#TEST_FLAG=False

if len(sys.argv) > 1:
    if not int(sys.argv[1]) in range(0, 2):
        QMessageBox.critical(None,"Error", f"{sys.argv[1]} Unknown Argument!")
        exit()
    elif int(sys.argv[1])==0:
        TEST_FLAG=False
    else:
        TEST_FLAG=True
ver = 0.9

# --- CONFIG ---
if TEST_FLAG:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'GOMS',
        'password': 'PGOMS',
        'database': 'garment_db',
        'autocommit': True
    }
else:
    DB_CONFIG = {
        'host': '10.68.182.221',
        'user': 'GOMS',
        'password': 'PGOMS',
        'database': 'garment_db',
        'autocommit': True
    }
    
LOG_FILE = 'garment_manager.log'

if TEST_FLAG:
    CUSTOMER_ID_FILE = os.path.join(os.path.dirname(__file__), 'customer_ids.json')
else:
    CUSTOMER_ID_FILE = r"\\BW-NAS02\App\BetaApp\GarmentMan\customer_ids.json"

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- DB CONNECTION ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        QMessageBox.critical(None, "DB Error", f"Could not connect to database: {e}")
        sys.exit(1)

# --- DARK MATERIAL THEME ---
def apply_dark_material_palette(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 239, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(38, 50, 56))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(55, 71, 79))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(236, 239, 241))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 239, 241))
    palette.setColor(QPalette.ColorRole.Button, QColor(48, 63, 159))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 239, 241))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(30, 136, 229))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyle("Fusion")
    app.setStyleSheet('''
        QPushButton {
            background-color: #3949ab;
            color: #fff;
            border-radius: 6px;
            padding: 10px 18px;
            font-size: 15px;
        }
        QPushButton:hover {
            background-color: #5c6bc0;
        }
        QPushButton:pressed {
            background-color: #283593;
        }
        QToolBar {
            background: #23272f;
            spacing: 10px;
        }
        QMainWindow {
            background: #212121;
        }
        QLabel {
            color: #eceff1;
            font-size: 10px;
        }
        QComboBox {
            font-size: 10px;
            min-height: 18px; 
            max-height: 50px;
            combobox-popup: 0;
        }
        QSpinbox {
            font-family: Tahoma;
        }
        QMenu {
            background-color: lightGray; /* Sets the background color of the menu */
            color: black; /* Sets the default text color of menu items */
        }
        QMenu::item:selected {
            background-color: LightBlue; /* Sets the background color of a selected menu item */
            color: black; /* Sets the text color of a selected menu item */
        }
        QMenu::separator {
            height: 2px; /* Sets the height of separators */
            margin: 2px 2px 2px 2px; /* Sets the margins around separators */
        }
    ''')

# Helper function for date formatting
def format_ddmmyy(dt):
    if not dt:
        return ''
    if isinstance(dt, str):
        # Try to parse string
        try:
            if len(dt) >= 10:
                # Try YYYY-MM-DD
                d = datetime.strptime(dt[:10], '%Y-%m-%d')
                return d.strftime('%d/%m/%y')
        except Exception:
            return dt
    elif isinstance(dt, (datetime, date)):
        return dt.strftime('%d/%m/%y')
    return str(dt)

def format_ddmmyyhhmm(dt):
    if not dt:
        return ''
    if isinstance(dt, str):
        # Try to parse string
        try:
            if len(dt) >= 19:
                # Try YYYY-MM-DD HH:MM
                d = datetime.strptime(dt[:19], '%Y-%m-%d %H:%M')
                return d.strftime('%d/%m/%y , %H:%M')
        except Exception:
            return dt
    elif isinstance(dt, (datetime, date)):
        return dt.strftime('%d/%m/%y , %H:%M')
    return str(dt)

# Helper function for number formatting
def format_number(value, decimals=2):
    """Format numerical values to x,xxx.xx format"""
    if value is None or value == '':
        return f"0.{'0' * decimals}" if decimals > 0 else '0'
    try:
        # Convert to float and format
        num = float(value)
        if decimals == 0:
            return f"{int(num):,}"
        else:
            return f"{num:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)

def format_integer(value):
    """Format numerical values as integers (no decimal places)"""
    return format_number(value, decimals=0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Garment Order Management System"+(f" - v.{ver.__format__('.2f')} - TEST" if TEST_FLAG else ""))
        self.resize(1400, 900)
        self.setMinimumSize(1000, 700)
        
        # --- Debouncing for filters ---
        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filters)
        
        #context menu
        self.menu = None

        # --- Navigation Bar ---
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setFixedHeight(56)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        # Navigation actions
        self.tabs = [
            ("Fabric Invoice", "fabric"),
            ("Stitching Record", "stitching"),
            ("Packing List", "packing"),
            ("Group Bill", "group"),
            ("Audit Log", "audit")
        ]
        # Now create navigation actions for all tabs
        self.actions = {}
        for idx, (label, key) in enumerate(self.tabs):
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, tab_idx=idx: self.switch_tab(tab_idx))
            self.toolbar.addAction(act)
            self.actions[key] = act
        # --- Central Widget ---
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.stacked = QStackedWidget()
        self.layout.addWidget(self.stacked)

        # Set global button font and size to match treeview and be 15% smaller
        base_font = self.font()
        tree_font = QTreeWidget().font()
        small_font_size = int(tree_font.pointSize() * 0.85)
        button_style = f"""
            QPushButton {{
                font-size: {small_font_size}pt;
                min-height: 18px;
                max-height: 26px;
                padding: 2px 10px;
            }}
        """
        self.setStyleSheet(self.styleSheet() + button_style)

        # --- Content Tabs ---
        self.fabric_tab = QWidget()
        self.fabric_tab.setLayout(QVBoxLayout())
        # --- Fabric Invoice Tab UI ---
        fabric_layout = self.fabric_tab.layout()
        
        # Filter controls - single row with very small font
        filter_row = QHBoxLayout()
        
        # Customer filter
        customer_label = QLabel("Customer:")
        self.filter_customer_name = QComboBox()
        self.filter_customer_name.setEditable(True)
        self.filter_customer_name.setPlaceholderText("Customer")
        self.filter_customer_name.setFixedWidth(200)
        self.filter_customer_name.setMaxVisibleItems(10)
        
        filter_row.addWidget(customer_label,0)
        filter_row.addWidget(self.filter_customer_name,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # Fab Invoice filter
        fab_inv_label = QLabel("Fab Inv:")
        self.filter_fab_invoice_number = QComboBox()
        self.filter_fab_invoice_number.setEditable(True)
        self.filter_fab_invoice_number.setPlaceholderText("Fab Invoice #")
        self.filter_fab_invoice_number.setFixedWidth(100)
        self.filter_fab_invoice_number.setMaxVisibleItems(10)
        
        filter_row.addWidget(fab_inv_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_fab_invoice_number,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # Tax Invoice filter
        tax_inv_label = QLabel("Tax Inv:")
        self.filter_tax_invoice_number = QComboBox()
        self.filter_tax_invoice_number.setEditable(True)
        self.filter_tax_invoice_number.setPlaceholderText("Tax Invoice #")
        self.filter_tax_invoice_number.setMaxVisibleItems(10)
        self.filter_tax_invoice_number.setFixedWidth(100)
        
        filter_row.addWidget(tax_inv_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_tax_invoice_number,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # Item Code filter
        item_code_label = QLabel("Item:")
        self.filter_item_code = QComboBox()
        self.filter_item_code.setEditable(True)
        self.filter_item_code.setPlaceholderText("Item Code")
        self.filter_item_code.setFixedWidth(100)
        self.filter_item_code.setMaxVisibleItems(10)
        
        filter_row.addWidget(item_code_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_item_code,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # DN Number filter
        dn_label = QLabel("DN:")
        self.filter_dn_number = QComboBox()
        self.filter_dn_number.setEditable(True)
        self.filter_dn_number.setPlaceholderText("DN #")
        self.filter_dn_number.setFixedWidth(100)
        self.filter_dn_number.setMaxVisibleItems(10)
        
        filter_row.addWidget(dn_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_dn_number,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # Delivered Location filter
        location_label = QLabel("Location:")
        self.filter_delivered_location = QComboBox()
        self.filter_delivered_location.setEditable(True)
        self.filter_delivered_location.setPlaceholderText("Delivered Location")
        self.filter_delivered_location.setFixedWidth(100)
        self.filter_delivered_location.setMaxVisibleItems(10)
        
        filter_row.addWidget(location_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_delivered_location,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        filter_row.addSpacing(20)
        
        # Date From filter
        date_from_label = QLabel("From:")
        self.filter_date_from = QLineEdit()
        self.filter_date_from.setPlaceholderText("DD/MM/YY")
        self.filter_date_from.setFixedWidth(60)
        self.filter_date_from.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.filter_date_from.textChanged.connect(self.format_date_input)
        filter_row.addWidget(date_from_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_date_from,0,Qt.AlignmentFlag.AlignLeft)
        
        # Date To filter
        date_to_label = QLabel("To:")
        self.filter_date_to = QLineEdit()
        self.filter_date_to.setPlaceholderText("DD/MM/YY")
        self.filter_date_to.setFixedWidth(60)
        self.filter_date_to.setStyleSheet("font-size: 10px; min-height: 18px; max-height:18px;")
        self.filter_date_to.textChanged.connect(self.format_date_input)
        filter_row.addWidget(date_to_label,0,Qt.AlignmentFlag.AlignRight)
        filter_row.addWidget(self.filter_date_to,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        #filter_row.addSpacing(20)
        
        # Show fully consumed fabrics toggle
        self.show_consumed_checkbox = QCheckBox("Show Fully Consumed")
        self.show_consumed_checkbox.setToolTip("Show fabrics with 0 or negative pending amount")
        self.show_consumed_checkbox.setStyleSheet("font-size: 10px;")
        self.show_consumed_checkbox.stateChanged.connect(self.refresh_invoice_table)
        filter_row.addWidget(self.show_consumed_checkbox)
        
        #Add Black Item
        filter_row.addItem(QSpacerItem(1,18,QSizePolicy.Policy.Expanding))
        
        # Clear filter button
        clear_filter_btn = QPushButton("Clear Filter")
        clear_filter_btn.setFixedWidth(100)
        clear_filter_btn.setFixedHeight(18)
        clear_filter_btn.setStyleSheet("font-size: 10px;")
        clear_filter_btn.setToolTip("Clear all filters")
        clear_filter_btn.clicked.connect(self.clear_fabric_filters)
        filter_row.addWidget(clear_filter_btn)
        
        fabric_layout.addLayout(filter_row)
        # Table for invoices
        self.invoice_table = QTableWidget(0, 14)
        
        #Context Menu
        self.invoice_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)     # +++
        self.invoice_table.customContextMenuRequested.connect(self.generateMenu) # +++
        self.invoice_table.viewport().installEventFilter(self)
        
        self.invoice_table.setHorizontalHeaderLabels([
            "Date", "Short Name", "Invoice Number", "Tax Invoice #", "Item Code", "Color", "Delivery Note", "In Stock", "Used", "Pending", "Price", "Total", "Delivered Location", "Line ID"
        ])
        
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Set default column widths
        invoice_col_widths = [80, 120, 100, 100, 90, 70, 90, 80, 90, 80, 60, 80, 110, 80]
        for i, w in enumerate(invoice_col_widths):
            self.invoice_table.setColumnWidth(i, w)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoice_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Flag to prevent itemChanged signal during table refresh
        self._refreshing_invoice_table = False
        
        fabric_layout.addWidget(self.invoice_table)
        # Action buttons
        action_row = QHBoxLayout()
        assign_btn = QPushButton("Assign Delivered Location")
        assign_btn.clicked.connect(self.assign_delivered_location)
        action_row.addWidget(assign_btn)
        assign_tax_btn = QPushButton("Assign Tax Invoice Number")
        assign_tax_btn.clicked.connect(self.assign_tax_invoice_number)
        action_row.addWidget(assign_tax_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_invoice_table)
        action_row.addWidget(refresh_btn)
        create_stitching_btn = QPushButton("Create Stitching Record")
        create_stitching_btn.clicked.connect(self.open_stitching_record_dialog)
        action_row.addWidget(create_stitching_btn)
        # Add Customer IDs button to fabric invoice tab's action row
        customer_id_btn = QPushButton("Customer IDs")
        customer_id_btn.setFixedWidth(110)
        customer_id_btn.setToolTip("Manage Customer IDs for data import")
        customer_id_btn.clicked.connect(self.open_customer_id_dialog)
        action_row.addWidget(customer_id_btn)
        # Add manual invoice line management buttons (no import button here)
        add_invoice_line_btn = QPushButton("Add Invoice Line")
        add_invoice_line_btn.clicked.connect(self.open_add_invoice_line_dialog)
        action_row.addWidget(add_invoice_line_btn)
        delete_invoice_line_btn = QPushButton("Delete Selected Invoice")
        delete_invoice_line_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_invoice_line_btn.clicked.connect(self.delete_invoice_line)
        action_row.addWidget(delete_invoice_line_btn)
        fabric_layout.addLayout(action_row)
        # Add to stacked widget
        self.stacked.addWidget(self.fabric_tab)
        
        # --- Stitching Record Tab UI ---
        self.stitching_tab = QWidget()
        self.stitching_tab.setLayout(QVBoxLayout())
        stitching_layout = self.stitching_tab.layout()
        # Filter controls - single row with compact design
        stitch_filter_row = QGridLayout() #QHBoxLayout()
        #stitch_filter_row.setColumnMinimumWidth(2,120)
        #stitch_filter_row.setColumnStretch(2,0)
        
        # PL # filter
        pl_label = QLabel("PL #:")
        pl_label.setFixedWidth(20)
        self.filter_pl_number = QComboBox()
        self.filter_pl_number.setEditable(True)
        self.filter_pl_number.setPlaceholderText("PL #")
        self.filter_pl_number.setFixedWidth(100)
        self.filter_pl_number.setMaxVisibleItems(10)
        
        stitch_filter_row.addWidget(pl_label,0,0)
        stitch_filter_row.addWidget(self.filter_pl_number,0,1,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        #stitch_filter_row.addSpacing(20)
        stitch_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),0,2)
        
        # Fabric filter
        fabric_label = QLabel("Fabric:")
        fabric_label.setFixedWidth(30)
        self.filter_fabric_name = QComboBox()
        self.filter_fabric_name.setEditable(True)
        self.filter_fabric_name.setPlaceholderText("Fabric")
        self.filter_fabric_name.setFixedWidth(120)
        self.filter_fabric_name.setMaxVisibleItems(10)
        
        stitch_filter_row.addWidget(fabric_label,0,3,Qt.AlignmentFlag.AlignRight)
        stitch_filter_row.addWidget(self.filter_fabric_name,0,4,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        #stitch_filter_row.addSpacing(20)
        stitch_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),0,5)
        
        # Customer filter
        customer_label = QLabel("Customer:")
        customer_label.setFixedWidth(50)
        self.filter_customer_stitch = QComboBox()
        self.filter_customer_stitch.setEditable(True)
        self.filter_customer_stitch.setPlaceholderText("Customer")
        self.filter_customer_stitch.setFixedWidth(200)
        self.filter_customer_stitch.setMaxVisibleItems(10)
        
        stitch_filter_row.addWidget(customer_label,0,6,Qt.AlignmentFlag.AlignRight)
        stitch_filter_row.addWidget(self.filter_customer_stitch,0,7,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        #stitch_filter_row.addSpacing(20)
        stitch_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),0,8)
        
        # Serial # filter
        serial_label = QLabel("Serial #:")
        serial_label.setFixedWidth(40)
        self.filter_serial_number = QComboBox()
        self.filter_serial_number.setEditable(True)
        self.filter_serial_number.setPlaceholderText("Serial #")
        self.filter_serial_number.setFixedWidth(120)
        self.filter_serial_number.setMaxVisibleItems(10)
        
        stitch_filter_row.addWidget(serial_label,0,11,Qt.AlignmentFlag.AlignRight)
        stitch_filter_row.addWidget(self.filter_serial_number,0,12,Qt.AlignmentFlag.AlignLeft)
        
        #Add blank space
        #stitch_filter_row.addSpacing(20)
        stitch_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),0,13)
        
        # Show radio buttons
        show_label = QLabel("Show:")
        show_label.setFixedWidth(30)
        stitch_filter_row.addWidget(show_label,0,14,Qt.AlignmentFlag.AlignRight)
        self.show_grouped_var = QButtonGroup()
        self.show_non_grouped = QRadioButton("In-Stock")
        self.show_non_grouped.setFixedWidth(70)
        self.show_non_grouped.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.show_grouped = QRadioButton("Delivered")
        self.show_grouped.setFixedWidth(70)
        self.show_grouped.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.show_all = QRadioButton("All")
        self.show_all.setFixedWidth(70)
        self.show_all.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.show_all.setChecked(True)
        self.show_grouped_var.addButton(self.show_non_grouped)
        self.show_grouped_var.addButton(self.show_grouped)
        self.show_grouped_var.addButton(self.show_all)
        stitch_filter_row.addWidget(self.show_non_grouped,0,15)
        stitch_filter_row.addWidget(self.show_grouped,0,16)
        stitch_filter_row.addWidget(self.show_all,0,17)
        
        #Add expanding space
        stitch_filter_row.addItem(QSpacerItem(18,18,QSizePolicy.Policy.Expanding),0,18)
        
        # Clear filter button
        clear_stitch_filter_btn = QPushButton("Clear Filter")
        clear_stitch_filter_btn.setFixedWidth(100)
        clear_stitch_filter_btn.setFixedHeight(18)
        clear_stitch_filter_btn.setStyleSheet("font-size: 10px;")
        clear_stitch_filter_btn.setToolTip("Clear all filters")
        clear_stitch_filter_btn.clicked.connect(self.clear_stitching_filters)
        stitch_filter_row.addWidget(clear_stitch_filter_btn,0,19)
        
        stitching_layout.addLayout(stitch_filter_row)
        # Tree for stitching records
        self.stitching_tree = QTreeWidget()
        
        #Context Menu
        self.stitching_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)     # +++
        self.stitching_tree.customContextMenuRequested.connect(self.generateMenu) # +++
        self.stitching_tree.viewport().installEventFilter(self)
        
        
        self.stitching_tree.setHeaderLabels([
            "PL #", "Serial #", "Garment", "Fabric", "Color", "Customer", "Tax Inv #", "Fabric Inv.", "Fabric DN.", "Fab Used", "Fab Cost", "Fab Value", "S", "M", "L", "XL", "XXL", "XXXL", "Total Qty", "Sew Cost", "Sew Value", "Yd/Pcs", "Grmt Cost", "Created At"
        ])
        self.stitching_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Set default column widths
        stitching_col_widths = [70, 90, 110, 90, 60, 100, 90, 90, 90, 80, 80, 120, 32, 32, 32, 36, 38, 40, 60, 80, 110, 60, 80, 110]
        for i, w in enumerate(stitching_col_widths):
            self.stitching_tree.setColumnWidth(i, w)
        self.stitching_tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.stitching_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        self.stitching_tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        stitching_layout.addWidget(self.stitching_tree)
        # Action buttons
        stitch_action_row = QHBoxLayout()
        generate_group_packing_btn = QPushButton("Generate Group Packing List")
        generate_group_packing_btn.clicked.connect(self.create_grouped_packing_list)
        stitch_action_row.addWidget(generate_group_packing_btn)
        refresh_stitch_btn = QPushButton("Refresh")
        refresh_stitch_btn.clicked.connect(self.refresh_stitching_lines_table)
        stitch_action_row.addWidget(refresh_stitch_btn)
        stitch_action_row.addStretch()
        stitch_action_row.addWidget(QLabel("Tip: Select stitching records and click 'Generate Group Packing List' to create a new packing list."))
        delete_stitching_btn = QPushButton("Delete Selected Stitching")
        delete_stitching_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_stitching_btn.clicked.connect(self.delete_stitching_record)
        stitch_action_row.addWidget(delete_stitching_btn)
        stitching_layout.addLayout(stitch_action_row)
        self.stacked.addWidget(self.stitching_tab)
        # --- Packing List Tab UI ---
        self.packing_tab = QWidget()
        self.packing_tab.setLayout(QVBoxLayout())
        packing_layout = self.packing_tab.layout()
        # Filter controls - single row with compact design
        packing_filter_row = QHBoxLayout()

        # PL# filter
        pl_label = QLabel("PL#:")
        pl_label.setFixedWidth(17)
        self.pl_filter_serial = QComboBox()
        self.pl_filter_serial.setEditable(True)
        self.pl_filter_serial.setPlaceholderText("PL#")
        self.pl_filter_serial.setFixedWidth(90)
        self.pl_filter_serial.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(pl_label,0)
        packing_filter_row.addWidget(self.pl_filter_serial,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(5,18,QSizePolicy.Policy.Fixed))

        # Serial # filter
        serial_label = QLabel("Serial#:")
        serial_label.setFixedWidth(31)
        self.pl_filter_stitch_serial = QComboBox()
        self.pl_filter_stitch_serial.setEditable(True)
        self.pl_filter_stitch_serial.setPlaceholderText("Serial #")
        self.pl_filter_stitch_serial.setFixedWidth(90)
        self.pl_filter_stitch_serial.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(serial_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_stitch_serial,0,Qt.AlignmentFlag.AlignLeft,)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(5,18,QSizePolicy.Policy.Fixed),5)

        # Fabric filter
        fabric_label = QLabel("Fab.:")
        fabric_label.setFixedWidth(22)
        self.pl_filter_fabric = QComboBox()
        self.pl_filter_fabric.setEditable(True)
        self.pl_filter_fabric.setPlaceholderText("Fabric")
        self.pl_filter_fabric.setFixedWidth(90)
        self.pl_filter_fabric.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(fabric_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_fabric,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(5,18,QSizePolicy.Policy.Fixed),8)

        # Customer filter
        customer_label = QLabel("Cust.:")
        customer_label.setFixedWidth(31)
        self.pl_filter_customer = QComboBox()
        self.pl_filter_customer.setEditable(True)
        self.pl_filter_customer.setPlaceholderText("Customer")
        self.pl_filter_customer.setFixedWidth(150)
        self.pl_filter_customer.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(customer_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_customer,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed),11)

        # Tax Inv # filter
        taxinv_label = QLabel("Tax Inv #:")
        taxinv_label.setFixedWidth(40)
        self.pl_filter_taxinv = QComboBox()
        self.pl_filter_taxinv.setEditable(True)
        self.pl_filter_taxinv.setPlaceholderText("Tax Inv #")
        self.pl_filter_taxinv.setFixedWidth(90)
        self.pl_filter_taxinv.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(taxinv_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_taxinv,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),14)

        # Fabric Inv filter
        fabinv_label = QLabel("Fab. Inv:")
        fabinv_label.setFixedWidth(40)
        self.pl_filter_fabinv = QComboBox()
        self.pl_filter_fabinv.setEditable(True)
        self.pl_filter_fabinv.setPlaceholderText("Fabric Inv")
        self.pl_filter_fabinv.setFixedWidth(90)
        self.pl_filter_fabinv.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(fabinv_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_fabinv,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),17)

        # Fabric DN filter
        fabdn_label = QLabel("Fab. DN:")
        fabdn_label.setFixedWidth(40)
        self.pl_filter_fabdn = QComboBox()
        self.pl_filter_fabdn.setEditable(True)
        self.pl_filter_fabdn.setPlaceholderText("Fabric DN")
        self.pl_filter_fabdn.setFixedWidth(80)
        self.pl_filter_fabdn.setMaxVisibleItems(10)
        
        packing_filter_row.addWidget(fabdn_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_fabdn,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),20)

        # Date From filter
        date_from_label = QLabel("From:")
        date_from_label.setFixedWidth(25)
        self.pl_filter_date_from = QLineEdit()
        self.pl_filter_date_from.setPlaceholderText("DD/MM/YY")
        self.pl_filter_date_from.setFixedWidth(60)
        self.pl_filter_date_from.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.pl_filter_date_from.textChanged.connect(self.format_date_input)
        
        packing_filter_row.addWidget(date_from_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_date_from,0,Qt.AlignmentFlag.AlignLeft)

        # Date To filter
        date_to_label = QLabel("To:")
        date_to_label.setFixedWidth(20)
        self.pl_filter_date_to = QLineEdit()
        self.pl_filter_date_to.setPlaceholderText("DD/MM/YY")
        self.pl_filter_date_to.setFixedWidth(60)
        self.pl_filter_date_to.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.pl_filter_date_to.textChanged.connect(self.format_date_input)
        
        packing_filter_row.addWidget(date_to_label,0,Qt.AlignmentFlag.AlignRight)
        packing_filter_row.addWidget(self.pl_filter_date_to,0,Qt.AlignmentFlag.AlignLeft)
        
        #Add space cell
        packing_filter_row.addSpacerItem(QSpacerItem(5,18,QSizePolicy.Policy.Fixed))
        #packing_filter_row.addItem(QSpacerItem(20,18,QSizePolicy.Policy.Fixed),25)

        # Billed/Unbilled/All radio toggle
        show_label = QLabel("Show:")
        show_label.setFixedWidth(30)
        packing_filter_row.addWidget(show_label,0,Qt.AlignmentFlag.AlignRight)
        
        self.pl_show_billed_var = QButtonGroup()
        self.pl_show_unbilled = QRadioButton("Unbilled")
        self.pl_show_unbilled.setFixedWidth(55)
        self.pl_show_unbilled.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.pl_show_billed = QRadioButton("Billed")
        self.pl_show_billed.setFixedWidth(45)
        self.pl_show_billed.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.pl_show_all = QRadioButton("All")
        self.pl_show_all.setFixedWidth(30)
        self.pl_show_all.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.pl_show_unbilled.setChecked(True)
        self.pl_show_billed_var.addButton(self.pl_show_unbilled)
        self.pl_show_billed_var.addButton(self.pl_show_billed)
        self.pl_show_billed_var.addButton(self.pl_show_all)
        packing_filter_row.addWidget(self.pl_show_unbilled,0,Qt.AlignmentFlag.AlignLeft)
        packing_filter_row.addWidget(self.pl_show_billed,0,Qt.AlignmentFlag.AlignLeft)
        packing_filter_row.addWidget(self.pl_show_all,0,Qt.AlignmentFlag.AlignLeft)
        # Packing List radio toggle (remove debouncing)
        self.pl_show_billed_var.buttonClicked.connect(self.refresh_packing_list_table)
        # Stitching Record radio toggle (already immediate, but ensure no debouncing is used)
        self.show_grouped_var.buttonClicked.connect(self.refresh_stitching_lines_table)
        
        #Add space cell
        #packing_filter_row.addItem(QSpacerItem(1,18,QSizePolicy.Policy.Expanding),30)
        #Add Black Item
        packing_filter_row.addSpacerItem(QSpacerItem(1,18,QSizePolicy.Policy.Expanding))
        # Clear filter button
        clear_packing_filter_btn = QPushButton("Clear Filter")
        clear_packing_filter_btn.setFixedWidth(100)
        clear_packing_filter_btn.setFixedHeight(18)
        clear_packing_filter_btn.setStyleSheet("font-size: 10px;")
        clear_packing_filter_btn.setToolTip("Clear all filters")
        clear_packing_filter_btn.clicked.connect(self.clear_packing_filters)
        packing_filter_row.addWidget(clear_packing_filter_btn,0)

        packing_layout.addLayout(packing_filter_row)
        # Tree for packing lists
        self.packing_tree = QTreeWidget()     
        
        #Context Menu
        self.packing_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)     # +++
        self.packing_tree.customContextMenuRequested.connect(self.generateMenu) # +++
        self.packing_tree.viewport().installEventFilter(self)
           
        self.packing_tree.setHeaderLabels([
            "PL #", "Serial #", "Garment", "Fabric", "Color", "Customer", "Tax Inv #", "Fabric Inv.", "Fabric DN.", "Fab Used", "Fab Cost", "Fab Value", "S", "M", "L", "XL", "XXL", "XXXL", "Total Qty", "Sew Cost", "Sew Value", "Created At"
        ])
        self.packing_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        packing_col_widths = [70, 90, 110, 90, 60, 100, 90, 90, 90, 80, 80, 120, 32, 32, 32, 36, 38, 40, 60, 80, 110, 110]
        for i, w in enumerate(packing_col_widths):
            self.packing_tree.setColumnWidth(i, w)
        self.packing_tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.packing_tree.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)
        self.packing_tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        packing_layout.addWidget(self.packing_tree)
        # Action buttons
        packing_action_row = QHBoxLayout()
        view_packing_btn = QPushButton("View Packing List")
        view_packing_btn.clicked.connect(self.view_packing_list_pdf_from_tree)
        packing_action_row.addWidget(view_packing_btn)
        create_group_billing_btn = QPushButton("Group and Create Billing Note")
        create_group_billing_btn.clicked.connect(self.create_group_billing_note)
        packing_action_row.addWidget(create_group_billing_btn)
        refresh_packing_btn = QPushButton("Refresh")
        refresh_packing_btn.clicked.connect(self.refresh_packing_list_table)
        packing_action_row.addWidget(refresh_packing_btn)
        assign_tax_btn = QPushButton("Assign Tax Invoice #")
        assign_tax_btn.clicked.connect(self.assign_tax_invoice_number_packing)
        packing_action_row.addWidget(assign_tax_btn)
        packing_action_row.addStretch()
        packing_action_row.addWidget(QLabel("Tip: Select packing lists and click 'View Packing List' to view PDFs or 'Group and Create Billing Note' to create billing notes."))
        delete_packing_btn = QPushButton("Delete Selected Packing List")
        delete_packing_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_packing_btn.clicked.connect(self.delete_packing_list)
        packing_action_row.addWidget(delete_packing_btn)
        packing_layout.addLayout(packing_action_row)
        self.stacked.addWidget(self.packing_tab)
        # --- Group Bill Tab UI ---
        self.group_tab = QWidget()
        self.group_tab.setLayout(QVBoxLayout())
        group_layout = self.group_tab.layout()
        # Filter controls
        group_filter_row = QHBoxLayout()
        # Bill #
        bill_label = QLabel("Bill #:")
        bill_label.setFixedWidth(23)
        self.gb_filter_group = QComboBox()
        self.gb_filter_group.setEditable(True)
        self.gb_filter_group.setPlaceholderText("Bill #")
        self.gb_filter_group.setFixedWidth(90)
        group_filter_row.addWidget(bill_label)
        group_filter_row.addWidget(self.gb_filter_group,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # PL #
        pl_label = QLabel("PL #:")
        pl_label.setFixedWidth(20)
        self.gb_filter_pl = QComboBox()
        self.gb_filter_pl.setEditable(True)
        self.gb_filter_pl.setPlaceholderText("PL #")
        self.gb_filter_pl.setFixedWidth(90)
        group_filter_row.addWidget(pl_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_pl,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Fabric
        fabric_label = QLabel("Fabric:")
        fabric_label.setFixedWidth(30)
        self.gb_filter_fabric = QComboBox()
        self.gb_filter_fabric.setEditable(True)
        self.gb_filter_fabric.setPlaceholderText("Fabric")
        self.gb_filter_fabric.setFixedWidth(90)
        group_filter_row.addWidget(fabric_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_fabric,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Customer
        customer_label = QLabel("Customer:")
        customer_label.setFixedWidth(45)
        self.gb_filter_customer = QComboBox()
        self.gb_filter_customer.setEditable(True)
        self.gb_filter_customer.setPlaceholderText("Customer")
        self.gb_filter_customer.setFixedWidth(200)
        group_filter_row.addWidget(customer_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_customer,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Tax Inv #
        taxinv_label = QLabel("Tax Inv #:")
        taxinv_label.setFixedWidth(40)
        self.gb_filter_taxinv = QComboBox()
        self.gb_filter_taxinv.setEditable(True)
        self.gb_filter_taxinv.setPlaceholderText("Tax Inv #")
        self.gb_filter_taxinv.setFixedWidth(90)
        group_filter_row.addWidget(taxinv_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_taxinv,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Fabric Inv #
        fabinv_label = QLabel("Fabric Inv #:")
        fabinv_label.setFixedWidth(50)
        self.gb_filter_fabinv = QComboBox()
        self.gb_filter_fabinv.setEditable(True)
        self.gb_filter_fabinv.setPlaceholderText("Fabric Inv #")
        self.gb_filter_fabinv.setFixedWidth(90)
        group_filter_row.addWidget(fabinv_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_fabinv,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Fabric DN
        fabdn_label = QLabel("Fabric DN:")
        fabdn_label.setFixedWidth(50)
        self.gb_filter_fabdn = QComboBox()
        self.gb_filter_fabdn.setEditable(True)
        self.gb_filter_fabdn.setPlaceholderText("Fabric DN")
        self.gb_filter_fabdn.setFixedWidth(90)
        group_filter_row.addWidget(fabdn_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_fabdn,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Black Item
        group_filter_row.addSpacerItem(QSpacerItem(10,18,QSizePolicy.Policy.Fixed))
        
        # Date From
        date_from_label = QLabel("From:")
        date_from_label.setFixedWidth(25)
        self.gb_filter_date_from = QLineEdit()
        self.gb_filter_date_from.setPlaceholderText("DD/MM/YY")
        self.gb_filter_date_from.setFixedWidth(60)
        self.gb_filter_date_from.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.gb_filter_date_from.textChanged.connect(self.format_date_input)
        group_filter_row.addWidget(date_from_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_date_from,alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Date To
        date_to_label = QLabel("To:")
        date_to_label.setFixedWidth(17)
        self.gb_filter_date_to = QLineEdit()
        self.gb_filter_date_to.setPlaceholderText("DD/MM/YY")
        self.gb_filter_date_to.setFixedWidth(60)
        self.gb_filter_date_to.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.gb_filter_date_to.textChanged.connect(self.format_date_input)
        group_filter_row.addWidget(date_to_label,alignment=Qt.AlignmentFlag.AlignRight)
        group_filter_row.addWidget(self.gb_filter_date_to,alignment=Qt.AlignmentFlag.AlignLeft)
        
        #Add Blank Item
        group_filter_row.addItem(QSpacerItem(10,18,QSizePolicy.Policy.Expanding))
        
        # Clear filter button
        clear_group_filter_btn = QPushButton("Clear Filter")
        clear_group_filter_btn.setStyleSheet("font-size: 10px;")
        clear_group_filter_btn.setFixedWidth(100)
        clear_group_filter_btn.setToolTip("Clear all filters")
        clear_group_filter_btn.clicked.connect(self.clear_group_filters)
        group_filter_row.addWidget(clear_group_filter_btn)
        group_layout.addLayout(group_filter_row)
        
        # Tree for group bills
        self.gb_tree = QTreeWidget()
        
        #Context Menu
        self.gb_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)     # +++
        self.gb_tree.customContextMenuRequested.connect(self.generateMenu) # +++
        self.gb_tree.viewport().installEventFilter(self)
        
        self.gb_tree.setHeaderLabels([
            "Bill #", "PL #", "Garment", "Fabric", "Color", "Customer", "Tax Inv #", "Fabric Inv #", "Fabric DN", "Fab Used", "Fab Cost", "Fab Value", "S", "M", "L", "XL", "XXL", "XXXL", "Total Qty", "Sew Cost", "Sew Value", "Created At"
        ])
        self.gb_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        gb_col_widths = [70, 90, 110, 90, 60, 100, 90, 90, 90, 80, 80, 120, 32, 32, 32, 36, 38, 40, 60, 80, 110, 110]
        for i, w in enumerate(gb_col_widths):
            self.gb_tree.setColumnWidth(i, w)
        self.gb_tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.gb_tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        group_layout.addWidget(self.gb_tree)
        # Action buttons
        group_action_row = QHBoxLayout()
        gb_pdf_btn = QPushButton("View PDF for Selected Group")
        gb_pdf_btn.clicked.connect(self.on_gb_pdf)
        group_action_row.addWidget(gb_pdf_btn)
        refresh_gb_btn = QPushButton("Refresh")
        refresh_gb_btn.clicked.connect(self.refresh_group_bill_table)
        group_action_row.addWidget(refresh_gb_btn)
        group_action_row.addStretch()
        group_action_row.addWidget(QLabel("Tip: Select a group and click to view PDFs."))
        delete_group_btn = QPushButton("Delete Selected Group")
        delete_group_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_group_btn.clicked.connect(self.delete_group_bill)
        group_action_row.addWidget(delete_group_btn)
        group_layout.addLayout(group_action_row)
        self.stacked.addWidget(self.group_tab)
        
        # --- Audit Log Tab UI ---
        self.audit_tab = QWidget()
        self.audit_tab.setLayout(QVBoxLayout())
        audit_layout = self.audit_tab.layout()
        # Filter controls
        filter_row = QHBoxLayout()
        self.audit_filter_user = QComboBox()
        self.audit_filter_user.setEditable(True)
        self.audit_filter_user.setPlaceholderText("User")
        self.audit_filter_user.setFixedWidth(120)
        filter_row.addWidget(QLabel("User:"))
        filter_row.addWidget(self.audit_filter_user)
        
        filter_row.addSpacerItem(QSpacerItem(30,18,QSizePolicy.Policy.Fixed))
        
        self.audit_filter_action = QComboBox()
        self.audit_filter_action.setEditable(True)
        self.audit_filter_action.setPlaceholderText("Action")
        self.audit_filter_action.setFixedWidth(120)        
        filter_row.addWidget(QLabel("Action:"))
        filter_row.addWidget(self.audit_filter_action)
        
        filter_row.addSpacerItem(QSpacerItem(30,18,QSizePolicy.Policy.Fixed))
        
        self.audit_filter_entity = QComboBox()
        self.audit_filter_entity.setEditable(True)
        self.audit_filter_entity.setPlaceholderText("Entity")
        self.audit_filter_entity.setFixedWidth(120)        
        filter_row.addWidget(QLabel("Entity:"))
        filter_row.addWidget(self.audit_filter_entity)
        
        filter_row.addSpacerItem(QSpacerItem(30,18,QSizePolicy.Policy.Fixed))
        
        # Date From filter
        date_from_label = QLabel("From:")
        self.audit_filter_date_from = QLineEdit()
        self.audit_filter_date_from.setPlaceholderText("DD/MM/YY")
        self.audit_filter_date_from.setFixedWidth(60)
        self.audit_filter_date_from.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.audit_filter_date_from.textChanged.connect(self.format_date_input)
        filter_row.addWidget(date_from_label)
        filter_row.addWidget(self.audit_filter_date_from)
        
        # Date To filter
        date_to_label = QLabel("To:")
        self.audit_filter_date_to = QLineEdit()
        self.audit_filter_date_to.setPlaceholderText("DD/MM/YY")
        self.audit_filter_date_to.setFixedWidth(60)
        self.audit_filter_date_to.setStyleSheet("font-size: 10px; min-height: 18px; max-height: 18px;")
        self.audit_filter_date_to.textChanged.connect(self.format_date_input)
        filter_row.addWidget(date_to_label)
        filter_row.addWidget(self.audit_filter_date_to)
        
        filter_row.addSpacerItem(QSpacerItem(1,18,QSizePolicy.Policy.Expanding))
        
        # Clear filter button
        clear_filter_btn = QPushButton("Clear Filter")
        clear_filter_btn.setFixedWidth(100)
        clear_filter_btn.setFixedHeight(18)
        clear_filter_btn.setStyleSheet("font-size: 10px;")
        clear_filter_btn.setToolTip("Clear all filters")
        clear_filter_btn.clicked.connect(self.clear_audit_filters)
        filter_row.addWidget(clear_filter_btn)
        
        audit_layout.addLayout(filter_row)
        # Table for audit logs
        self.audit_table = QTableWidget(0, 7)
        self.audit_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Entity", "Entity ID", "Description", "Details"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        audit_col_widths = [140, 80, 80, 80, 100, 320, 70]
        for i, w in enumerate(audit_col_widths):
            self.audit_table.setColumnWidth(i, w)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.audit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        audit_layout.addWidget(self.audit_table)
        # Refresh button
        audit_action_row = QHBoxLayout()
        refresh_audit_btn = QPushButton("Refresh")
        refresh_audit_btn.clicked.connect(self.refresh_audit_log_table)
        audit_action_row.addWidget(refresh_audit_btn)
        audit_action_row.addStretch()
        audit_layout.addLayout(audit_action_row)
        self.stacked.addWidget(self.audit_tab)
        # Select first tab by default
        self.switch_tab(0)
        # Initialize database and populate tables
        self.init_database()
        # Connect double-click for stitching table
        self.stitching_tree.itemDoubleClicked.connect(self.on_stitching_double_click)
        # Initialize UI data after all methods are defined
        self.init_ui_data()
        self.customer_ids = []
        self.load_customer_ids()
        # --- User Management ---
        self.current_user = None
        self.is_admin = False
        # Add hidden customer ID list widget for internal use
        self.selected_customers_list = QListWidget()
        self.selected_customers_list.setVisible(False)  # Hide from main UI
        self.layout.addWidget(self.selected_customers_list)
        # Add Login/Logout buttons to toolbar
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedWidth(70)
        self.login_btn.clicked.connect(self.show_login_dialog)
        self.toolbar.addWidget(self.login_btn)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFixedWidth(70)
        self.logout_btn.clicked.connect(self.logout_user)
        self.toolbar.addWidget(self.logout_btn)
        self.logout_btn.setEnabled(False)
        # Show main UI but keep it disabled until login
        self.disable_main_ui()

        # Add IMP button and user label to the main navigation toolbar (self.toolbar)
        self.toolbar.setFixedHeight(40)
        #23272f;
        #eceff1;
        #transparent;
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: #23272f;
                border: none;
                spacing: 10px;
                padding: 0 10px;
                min-height: 40px;
                max-height: 40px;
            }
            QToolButton, QLabel {
                font-size: 14px;
                color: #ffffff;
                padding: 0 10px;
                min-height: 32px;
                max-height: 32px;
                background: transparent;
            }
            QToolButton:hover {
                background-color: #3949ab;
                color: #ffffff;
            }
        """)
        # Spacer to push IMP button and user label to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        imp_action = QAction("Import Invoice Data", self)
        imp_action.setToolTip("Import .dat file")
        imp_action.triggered.connect(self.import_dat_file)
        self.toolbar.addAction(imp_action)
        # User label styled to match toolbar
        self.user_label = QLabel()
        self.user_label.setText("Not logged in")
        self.user_label.setStyleSheet("font-size: 14px; color: #eceff1; padding: 0 10px; min-height: 32px; max-height: 32px; background: transparent;")
        self.toolbar.addWidget(self.user_label)
        # Now update the user label after it's created
        self.update_user_label()

    def init_ui_data(self):
        """Initialize all table data after all methods are defined"""
        self.refresh_invoice_table()
        self.refresh_stitching_lines_table()
        self.refresh_group_bill_table()
        self.refresh_packing_list_table()
        self.refresh_audit_log_table()

    def switch_tab(self, idx):
        try:
            # Check if index is valid
            if idx < 0 or idx >= self.stacked.count():
                logger.error(f"Invalid tab index: {idx}, max index: {self.stacked.count() - 1}")
                return
            
            self.stacked.setCurrentIndex(idx)
            for i, (label, key) in enumerate(self.tabs):
                if key in self.actions:
                    self.actions[key].setChecked(i == idx)
        except Exception as e:
            logger.error(f"Error switching to tab {idx}: {e}")
            # Don't crash the app, just log the error
    # --- Placeholder methods for signals ---
    def import_dat_file(self):
        self.load_customer_ids()
        if self.stacked.isHidden():
            return 
        if TEST_FLAG:
            default_dir = "C:/GarmentMan/"
        else:
            default_dir = r"\\bw-nas02\XeroFTP\Beta_backup"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .dat File", default_dir, "DAT files (*.dat);;All files (*)")
        if not file_path:
            return
        
        # Get selected customer IDs for filtering
        selected_customer_ids = self.get_selected_customer_ids()
        
        # If no customer IDs are selected, ask user if they want to proceed
        if not selected_customer_ids:
            reply = QMessageBox.question(
                self, 
                "No Customer IDs Selected", 
                "No customer IDs are selected for filtering. This will import ALL customers from the .dat file.\n\nDo you want to proceed with importing all customers?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            # Show which customer IDs will be imported
            QMessageBox.information(
                self, 
                "Customer Filter Active", 
                f"Only data for the following customer IDs will be imported:\n{', '.join(selected_customer_ids)}"
            )
        
        summary = []
        errors = []
        imported_count = 0
        skipped_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            QMessageBox.critical(self, "File Error", f"Could not read file: {e}")
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="Import",
                entity_id=file_path,
                description=f"Error reading .dat file: {str(e)}",
                details={"traceback": traceback.format_exc(), "file_path": file_path}
            )
            return
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Track invoice numbers and their line counts
        invoice_line_counts = {}
        
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(';')]
            if len(parts) < 14:
                errors.append(f"Line {idx+1}: Invalid format (expected 14 fields, got {len(parts)})")
                logger.warning(f"Line {idx+1}: Invalid format: {line}")
                continue
            
            # Map fields
            tax = parts[0]
            short_name = parts[1]
            customer_id = parts[2]
            date_raw = parts[3]
            invoice_number = parts[4]
            currency = parts[5]
            item_code = parts[6]
            item_details = parts[7]
            fabric_amount = parts[8]
            price_per_unit = parts[9]
            # total_value = parts[10]  # Don't parse total_value from file
            description = parts[11]
            vat = parts[12]
            # parts[13] is unused
            
            # Convert the padded customer ID from .dat file to regular format
            # .dat file has customer ID as 8-digit padded (e.g., "00000328")
            # User enters regular format (e.g., "328")
            try:
                # Remove leading zeros and convert to integer, then back to string
                customer_id_normalized = str(int(customer_id))
            except ValueError:
                # If conversion fails, use original customer_id
                customer_id_normalized = customer_id
            
            # Check if customer ID is in selected list (if filtering is active)
            if customer_id_normalized not in selected_customer_ids: #selected_customer_ids and 
                skipped_count += 1
                continue
            
            # Parse date (YYYYMMDD to YYYY-MM-DD)
            invoice_date = None
            if date_raw and len(date_raw) == 8:
                try:
                    invoice_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
                except Exception:
                    invoice_date = None
            
            # Calculate total value from price × quantity
            try:
                fabric_qty = float(fabric_amount or 0)
                unit_price = float(price_per_unit or 0)
                calculated_total_value = fabric_qty * unit_price
            except (ValueError, TypeError):
                calculated_total_value = 0.0
                logger.warning(f"Line {idx+1}: Could not calculate total value from fabric_amount={fabric_amount}, price_per_unit={price_per_unit}")
            
            # Remove customer validation for testing
            cursor.execute("SELECT id FROM customers WHERE customer_id=%s AND short_name=%s", (customer_id_normalized, short_name))
            customer = cursor.fetchone()
            if not customer:
                cursor.execute(
                    "INSERT INTO customers (customer_id, short_name, full_name, registration_date, is_active) VALUES (%s, %s, %s, %s, %s)",
                    (customer_id_normalized, short_name, short_name, None, True)
                )
                customer_db_id = cursor.lastrowid
            else:
                customer_db_id = customer['id']
            
            # Handle duplicate invoice numbers by adding line numbers
            if invoice_number in invoice_line_counts:
                invoice_line_counts[invoice_number] += 1
            else:
                invoice_line_counts[invoice_number] = 1
            modified_invoice_number = f"{invoice_number}-{invoice_line_counts[invoice_number]:02d}"
            
            # Insert or update invoice
            #cursor.execute("SELECT id FROM invoices WHERE invoice_number=%s AND customer_id=%s", (modified_invoice_number, customer_db_id))
            
            cursor.execute("SELECT id FROM invoices WHERE trim(invoice_number)=%s", (modified_invoice_number,))
            invoice = cursor.fetchone()
            if not invoice:
                cursor.execute(
                    "INSERT INTO invoices (invoice_number, customer_id, invoice_date, total_amount, status, tax_invoice_number) VALUES (%s, %s, %s, %s, %s, %s)",
                    (modified_invoice_number, customer_db_id, invoice_date, calculated_total_value, 'open', None)
                )
                invoice_id = cursor.lastrowid
            
            
                # Extract color and delivery note from item_details (robust handling)
                details_parts = [p.strip() for p in item_details.split('/') if p.strip()]
                color = details_parts[1] if len(details_parts) > 1 else ''
                delivery_note = ''
                if len(details_parts) > 2:
                    if details_parts[2] == '0' and len(details_parts) > 3:
                        delivery_note = details_parts[3]
                    else:
                        delivery_note = details_parts[2]
                
                # Insert invoice line
                try:
                    cursor.execute(
                        "INSERT INTO invoice_lines (invoice_id, item_name, quantity, unit_price, delivered_location, is_defective, color, delivery_note, yards_sent, yards_consumed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (invoice_id, item_code, float(fabric_amount or 0), float(price_per_unit or 0), None, False, color, delivery_note, float(fabric_amount or 0), 0.0)
                    )
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Line {idx+1}: DB error: {e}")
                    logger.error(f"Line {idx+1}: DB error: {e}")
            else:
                invoice_id = invoice['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Show import results
        result_msg = f"Import completed!\n\nImported: {imported_count} lines"
        if selected_customer_ids:
            result_msg += f"\nSkipped (not in selected customer IDs): {skipped_count} lines"
        if errors:
            result_msg += f"\n\nErrors:\n" + "\n".join(errors)
        
        QMessageBox.information(self, "Import Success", result_msg)
        self.refresh_invoice_table()
        # Log audit action for data import
        log_audit_action(
            user=self.current_user,
            action_type="IMPORT",
            entity="Invoice",
            entity_id=file_path,
            description=f"Imported .dat file '{file_path}'. Imported: {imported_count}, Skipped: {skipped_count}, Errors: {len(errors)}.",
            details={
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors,
                "selected_customer_ids": selected_customer_ids,
                "file_path": file_path
            }
        )
    def assign_delivered_location(self):
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select one or more invoice lines.")
            return
        location, ok = QInputDialog.getText(self, "Delivered Location", "Enter delivered location for selected lines:")
        if not ok or not location:
            return
        conn = get_db_connection()
        try:
            not_found = 0
            for row in selected_rows:
                invoice_number = self.invoice_table.item(row.row(), 2).text()
                item_name = self.invoice_table.item(row.row(), 4).text()
                color = self.invoice_table.item(row.row(), 5).text()
                # Use a new buffered cursor for UPDATE
                update_cursor = conn.cursor(dictionary=True, buffered=True)
                update_cursor.execute("""
                    UPDATE invoice_lines l
                    JOIN invoices i ON l.invoice_id = i.id
                    SET l.delivered_location=%s
                    WHERE i.invoice_number=%s AND l.item_name=%s AND l.color=%s
                """, (location, invoice_number, item_name, color))
                update_cursor.close()
                # Use a new buffered cursor for SELECT
                select_cursor = conn.cursor(dictionary=True, buffered=True)
                select_cursor.execute("""
                    SELECT l.id, l.delivered_location, l.item_name, l.color, i.invoice_number, c.short_name as customer_name
                    FROM invoice_lines l
                    JOIN invoices i ON l.invoice_id = i.id
                    LEFT JOIN customers c ON i.customer_id = c.id
                    WHERE i.invoice_number=%s AND l.item_name=%s AND l.color=%s
                """, (invoice_number, item_name, color))
                old_line = select_cursor.fetchone()
                select_cursor.close()
                if old_line:
                    pass
                else:
                    not_found += 1
            conn.commit()
            logger.info(f"Assigned delivered location '{location}' to {len(selected_rows)} lines.")
            if not_found > 0:
                QMessageBox.warning(self, "Warning", f"{not_found} selected line(s) could not be found in the database and were skipped.")
            # Log audit action for delivered location assignment
            log_audit_action(
                user=self.current_user,
                action_type="UPDATE",
                entity="InvoiceLine",
                entity_id=None,
                description=f"Assigned delivered location '{location}' to {len(selected_rows)} invoice lines.",
                details={
                    "location": location,
                    "lines": [
                        {
                            "invoice_number": self.invoice_table.item(row.row(), 2).text(),
                            "item_name": self.invoice_table.item(row.row(), 4).text(),
                            "color": self.invoice_table.item(row.row(), 5).text()
                        } for row in selected_rows
                    ]
                }
            )
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="InvoiceLine",
                entity_id=None,
                description=f"Error assigning delivered location: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            logger.error(f"Error assigning delivered location: {e}")
            QMessageBox.critical(self, "Error", f"Failed to assign delivered location: {e}")
        finally:
            conn.close()
        self.refresh_invoice_table()
        
    def assign_tax_invoice_number(self):
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection Error", "Please select one or more fabric invoice lines to assign tax invoice numbers.")
            return
        
        # Get unique invoice numbers from selected rows
        invoice_numbers = set()
        for row in selected_rows:
            invoice_number = self.invoice_table.item(row.row(), 2).text()
            invoice_numbers.add(invoice_number)
        
        if len(invoice_numbers) > 1:
            QMessageBox.warning(self, "Multiple Invoices", "Please select lines from only one invoice at a time.")
            return
        
        invoice_number = list(invoice_numbers)[0]
        
        # Extract base invoice number (remove line number suffix like -1, -2, etc.)
        base_invoice_number = invoice_number
        if '-' in invoice_number:
            base_invoice_number = invoice_number.split('-')[0]
        
        # Dialog to enter tax invoice number
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Assign Tax Invoice Number")
        dialog.setLabelText(f"Enter tax invoice number for invoice {base_invoice_number} (will apply to all lines):")
        dialog.setTextValue("")
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        # Add tooltip explaining the "0" functionality
        dialog.setToolTip("Enter a tax invoice number to assign it to all lines with this base invoice number.\nEnter '0' to clear/remove the tax invoice number.")
        
        ok = dialog.exec()
        tax_invoice_number = dialog.textValue().strip()
        
        if not ok:
            return
        
        # Update database - assign to all invoices with the same base invoice number
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # If user entered "0", clear the tax invoice number (set to NULL)
            if tax_invoice_number == "0":
                cursor.execute(
                    "UPDATE invoices SET tax_invoice_number = NULL WHERE invoice_number LIKE %s",
                    (f"{base_invoice_number}%",)
                )
                affected_rows = cursor.rowcount
                conn.commit()
                # Log audit action for clearing tax invoice number
                log_audit_action(
                    user=self.current_user,
                    action_type="UPDATE",
                    entity="Invoice",
                    entity_id=base_invoice_number,
                    description=f"Cleared tax invoice number for all invoices starting with {base_invoice_number}.",
                    details={"tax_invoice_number": None, "affected_invoices": base_invoice_number}
                )
            else:
                # Update all invoices that start with the base invoice number
                cursor.execute(
                    "UPDATE invoices SET tax_invoice_number = %s WHERE invoice_number LIKE %s",
                    (tax_invoice_number, f"{base_invoice_number}%")
                )
                affected_rows = cursor.rowcount
                conn.commit()
                # Log audit action for assigning tax invoice number
                log_audit_action(
                    user=self.current_user,
                    action_type="UPDATE",
                    entity="Invoice",
                    entity_id=base_invoice_number,
                    description=f"Assigned tax invoice number '{tax_invoice_number}' to all invoices starting with {base_invoice_number}.",
                    details={"tax_invoice_number": tax_invoice_number, "affected_invoices": base_invoice_number}
                )
            self.refresh_invoice_table()
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="Invoice",
                entity_id=base_invoice_number,
                description=f"Error assigning tax invoice number: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            logger.error(f"Error assigning tax invoice number: {e}")
            QMessageBox.critical(self, "Error", f"Failed to assign tax invoice number: {e}")
        finally:
            cursor.close()
            conn.close()

    def delete_all_invoices(self):
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete ALL invoices and related lines? This cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM invoice_lines")
            cursor.execute("DELETE FROM invoices")
            conn.commit()
            logger.info("All invoices and invoice lines deleted.")
            QMessageBox.information(self, "Success", "All invoices and invoice lines have been deleted.")
        except Exception as e:
            logger.error(f"Error deleting invoices: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete invoices: {e}")
        finally:
            cursor.close()
            conn.close()
        self.refresh_invoice_table()
        
    def refresh_invoice_table(self):
        # Set flag to prevent itemChanged signal during refresh
        self._refreshing_invoice_table = True
        # Clear table
        self.invoice_table.setRowCount(0)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT i.invoice_date, c.short_name, i.invoice_number, i.tax_invoice_number, l.id as line_id, l.item_name, l.color, l.delivery_note, l.quantity, l.unit_price, i.total_amount, l.delivered_location, l.id, l.yards_sent, l.yards_consumed
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            JOIN invoice_lines l ON l.invoice_id = i.id
            WHERE 1=1
        """
        
        # Add condition for pending amount based on checkbox
        if not self.show_consumed_checkbox.isChecked():
            query += " AND l.yards_sent > l.yards_consumed"
        params = []
        # Apply filters
        if self.filter_customer_name.currentText():
            query += " AND c.short_name LIKE %s"
            params.append(f"%{self.filter_customer_name.currentText()}%")
        if self.filter_fab_invoice_number.currentText():
            query += " AND i.invoice_number LIKE %s"
            params.append(f"%{self.filter_fab_invoice_number.currentText()}%")
        if self.filter_tax_invoice_number.currentText():
            query += " AND i.tax_invoice_number LIKE %s"
            params.append(f"%{self.filter_tax_invoice_number.currentText()}%")
        if self.filter_item_code.currentText():
            query += " AND l.item_name LIKE %s"
            params.append(f"%{self.filter_item_code.currentText()}%")
        if self.filter_dn_number.currentText():
            query += " AND l.delivery_note LIKE %s"
            params.append(f"%{self.filter_dn_number.currentText()}%")
        if self.filter_delivered_location.currentText():
            query += " AND l.delivered_location LIKE %s"
            params.append(f"%{self.filter_delivered_location.currentText()}%")
        date_from = self.filter_date_from.text().strip()
        date_to = self.filter_date_to.text().strip()
        if date_from:
            try:
                # Convert DD/MM/YY to YYYY-MM-DD
                if len(date_from) == 8 and date_from.count('/') == 2:
                    day, month, year = date_from.split('/')
                    # Convert 2-digit year to 4-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_from_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    query += " AND i.invoice_date >= %s"
                    params.append(date_from_iso)
            except (ValueError, IndexError):
                pass
        if date_to:
            try:
                # Convert DD/MM/YY to YYYY-MM-DD
                if len(date_to) == 8 and date_to.count('/') == 2:
                    day, month, year = date_to.split('/')
                    # Convert 2-digit year to 4-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_to_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    query += " AND i.invoice_date <= %s"
                    params.append(date_to_iso)
            except (ValueError, IndexError):
                pass
        query += " ORDER BY i.invoice_number DESC, l.id ASC"
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                date_val = format_ddmmyy(row['invoice_date'])
                yards_sent = row.get('yards_sent')
                if yards_sent is None:
                    yards_sent = row.get('quantity', 0) or 0
                yards_consumed = row.get('yards_consumed')
                if yards_consumed is None:
                    yards_consumed = 0
                pending = yards_sent - yards_consumed
                values = [
                    date_val if date_val else '',
                    row['short_name'],
                    row['invoice_number'],
                    row['tax_invoice_number'] or '',
                    row['item_name'],
                    row['color'] if row['color'] else '',
                    row['delivery_note'] if row['delivery_note'] else '',
                    format_number(yards_sent),
                    format_number(yards_consumed),
                    format_number(pending),
                    format_number(row['unit_price']),
                    format_number(row['total_amount']),
                    row['delivered_location'] if row['delivered_location'] else '',
                    str(row['line_id'])  # Hidden column for invoice line ID
                ]
                row_idx = self.invoice_table.rowCount()
                self.invoice_table.insertRow(row_idx)
                
                for col_idx, val in enumerate(values):
                    item = QTableWidgetItem(str(val))
                    
                    if int(col_idx) >= 7 and int(col_idx) <= 11:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        
                    if col_idx == len(values) - 1:
                        # Hide the ID column
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.invoice_table.setItem(row_idx, col_idx, item)
            if len(rows) > 0:
                # Hide the last column (ID)
                self.invoice_table.setColumnHidden(len(values) - 1, True)
        except Exception as e:
            logger.error(f"Error loading invoices: {e}")
        finally:
            cursor.close()
            conn.close()
        # Populate filter comboboxes with unique values
        self.populate_invoice_filters()
        # Reset flag after refresh is complete
        self._refreshing_invoice_table = False

    def apply_filters(self):
        """Debounced filter application - called after user stops typing"""
        current_tab = self.stacked.currentIndex()
        if current_tab == 0:  # Fabric Invoice tab
            self.refresh_invoice_table()
        elif current_tab == 1:  # Stitching Record tab
            self.refresh_stitching_lines_table()
        elif current_tab == 2:  # Packing List tab
            self.refresh_packing_list_table()
        elif current_tab == 3:  # Group Bill tab
            self.refresh_group_bill_table()
        elif current_tab == 4:  # Audit Log tab
            self.refresh_audit_log_table()

    def trigger_filter_update(self):
        """Trigger debounced filter update"""
        self.filter_timer.stop()
        self.filter_timer.start(500)  # 500ms delay

    def format_date_input(self):
        """Auto-format date input to DD/MM/YY format"""
        sender = self.sender()
        if not sender:
            return
        
        text = sender.text()
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, text))
        
        # Format as DD/MM/YY
        formatted = ""
        if len(digits_only) >= 1:
            formatted += digits_only[:2]
        if len(digits_only) >= 3:
            formatted += "/" + digits_only[2:4]
        if len(digits_only) >= 5:
            formatted += "/" + digits_only[4:6]
        
        # Update text if different
        if formatted != text:
            sender.setText(formatted)

    def populate_invoice_filters(self):
        def get_unique_column_values(col):
            conn = get_db_connection()
            cursor = conn.cursor()
            col_map = {
                'short_name': 'c.short_name',
                'invoice_number': 'i.invoice_number',
                'tax_invoice_number': 'i.tax_invoice_number',
                'item_name': 'l.item_name',
                'delivery_note': 'l.delivery_note',
                'delivered_location': 'l.delivered_location'
            }
            sql = f"SELECT DISTINCT {col_map[col]} FROM invoices i JOIN customers c ON i.customer_id = c.id JOIN invoice_lines l ON l.invoice_id = i.id ORDER BY {col_map[col]}"
            cursor.execute(sql)
            vals = [row[0] for row in cursor.fetchall() if row[0]]
            cursor.close()
            conn.close()
            return vals
        # Only repopulate if not currently filtering
        if not self.filter_customer_name.currentText():
            self.filter_customer_name.clear()
            self.filter_customer_name.addItem("")
            self.filter_customer_name.addItems(get_unique_column_values('short_name'))
        if not self.filter_fab_invoice_number.currentText():
            self.filter_fab_invoice_number.clear()
            self.filter_fab_invoice_number.addItem("")
            self.filter_fab_invoice_number.addItems(get_unique_column_values('invoice_number'))
        if not self.filter_tax_invoice_number.currentText():
            self.filter_tax_invoice_number.clear()
            self.filter_tax_invoice_number.addItem("")
            self.filter_tax_invoice_number.addItems(get_unique_column_values('tax_invoice_number'))
        if not self.filter_item_code.currentText():
            self.filter_item_code.clear()
            self.filter_item_code.addItem("")
            self.filter_item_code.addItems(get_unique_column_values('item_name'))
        if not self.filter_dn_number.currentText():
            self.filter_dn_number.clear()
            self.filter_dn_number.addItem("")
            self.filter_dn_number.addItems(get_unique_column_values('delivery_note'))
        if not self.filter_delivered_location.currentText():
            self.filter_delivered_location.clear()
            self.filter_delivered_location.addItem("")
            self.filter_delivered_location.addItems(get_unique_column_values('delivered_location'))
        # Connect filter changes to debounced update
        self.filter_customer_name.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_fab_invoice_number.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_tax_invoice_number.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_item_code.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_dn_number.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_delivered_location.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_date_from.textChanged.connect(self.trigger_filter_update)
        self.filter_date_to.textChanged.connect(self.trigger_filter_update)

    def clear_fabric_filters(self):
        """Clear all fabric invoice filters"""
        self.filter_customer_name.setCurrentText("")
        self.filter_fab_invoice_number.setCurrentText("")
        self.filter_tax_invoice_number.setCurrentText("")
        self.filter_item_code.setCurrentText("")
        self.filter_dn_number.setCurrentText("")
        self.filter_delivered_location.setCurrentText("")
        self.filter_date_from.clear()
        self.filter_date_to.clear()
        self.refresh_invoice_table()

    def clear_stitching_filters(self):
        """Clear all stitching record filters"""
        self.filter_pl_number.setCurrentText("")
        self.filter_fabric_name.setCurrentText("")
        self.filter_customer_stitch.setCurrentText("")
        self.filter_serial_number.setCurrentText("")
        self.show_all.setChecked(True)
        self.refresh_stitching_lines_table()

    def clear_packing_filters(self):
        """Clear all packing list filters"""
        self.pl_filter_serial.setCurrentText("")
        self.pl_filter_stitch_serial.setCurrentText("")
        self.pl_filter_fabric.setCurrentText("")
        self.pl_filter_customer.setCurrentText("")
        self.pl_filter_taxinv.setCurrentText("")
        self.pl_filter_fabinv.setCurrentText("")
        self.pl_filter_fabdn.setCurrentText("")
        self.pl_filter_date_from.clear()
        self.pl_filter_date_to.clear()
        self.pl_show_unbilled.setChecked(True)
        self.refresh_packing_list_table()

    def clear_group_filters(self):
        """Clear all group bill filters"""
        self.gb_filter_group.setCurrentText("")
        self.gb_filter_pl.setCurrentText("")
        self.gb_filter_fabric.setCurrentText("")
        self.gb_filter_customer.setCurrentText("")
        self.gb_filter_taxinv.setCurrentText("")
        self.gb_filter_fabinv.setCurrentText("")
        self.gb_filter_fabdn.setCurrentText("")
        self.gb_filter_date_from.clear()
        self.gb_filter_date_to.clear()
        self.refresh_group_bill_table()

    def clear_audit_filters(self):
        """Clear all audit log filters"""
        self.audit_filter_user.clear()
        self.audit_filter_action.clear()
        self.audit_filter_entity.clear()
        self.audit_filter_date_from.clear()
        self.audit_filter_date_to.clear()
        self.refresh_audit_log_table()

    def open_edit_pending_dialog(self):
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.information(self, "Selection Error", "Please select one fabric invoice lines to create a stitching record.")
            return
        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)
        id_item = self.invoice_table.item(selected_rows[0].row(), self.invoice_table.columnCount() - 1)
        if not id_item:
            QMessageBox.critical(self, "Error", "Could not determine invoice line ID.")
            conn.close()
            return

        invoice_line_id = id_item.text()
        print(f"invoice_line_id: {invoice_line_id}")
        cursor.execute("SELECT id FROM stitching_invoices WHERE invoice_line_id = %s", (invoice_line_id,))
        if cursor.fetchone():
            QMessageBox.warning(self, "Already Used", "Cannot edit pending amount, This invoice line is already used in a stitching record.")
            cursor.close()
            conn.close()
            return
        cursor.close()

        lines = []
        for row in selected_rows:
            invoice_number_full = self.invoice_table.item(row.row(), 2).text()
            cursor = conn.cursor(dictionary=True)
            print(invoice_number_full)
            cursor.execute(
                f"SELECT l.*, i.invoice_number FROM invoice_lines l JOIN invoices i ON l.invoice_id = i.id WHERE i.invoice_number='{invoice_number_full}' LIMIT 1")
                #, (invoice_number_full))
            rowdata = cursor.fetchone()
            cursor.close()
            if rowdata:
                lines.append(rowdata)
        from PyQt6.QtWidgets import QFormLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QDialogButtonBox, QLabel, QPushButton
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Pending Amount")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enter New Pending Amount:"))

        qty_vars = []
        for idx, line in enumerate(lines):
            hbox = QHBoxLayout()
            sent_amt = (line.get('yards_sent', 0) or 0)
            pending_amt = (line.get('yards_sent', 0) or 0) - (line.get('yards_consumed', 0) or 0)
            hbox.addWidget(QLabel(f"Invoice #{line['invoice_number']} | Item: {line['item_name']} | Pending: {pending_amt} yards (Max: {sent_amt})"))
            var = QDoubleSpinBox()
            var.setRange(0, sent_amt)
            var.setDecimals(2)
            var.setValue(0)
            hbox.addWidget(var)
            qty_vars.append(var)
            layout.addLayout(hbox)
        
        def submit():
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                qty = [v.value() for v in qty_vars]
                if any(c <= 0 for c in qty):
                    raise ValueError("Pending Amount must be positive.")
                # Generate serial number
                now = datetime.now()
                mm_yy = now.strftime('%m%y')
                
                for idx, line in enumerate(lines):
                    print(f"qty={qty[idx]} , id={line['id']}")
                    cursor.execute("UPDATE invoice_lines SET yards_consumed=quantity-%s WHERE id = %s", (qty[idx], line['id']))
                    line_id = line['id']
                    line_item_name = line['item_name']
                    amt = qty[idx]
                conn.commit()
                # Log audit action for stitching record creation
                log_audit_action(
                    user=self.current_user,
                    action_type="Update",
                    entity="Invoice_Line",
                    entity_id=line_id,
                    description=f"Update {line_id} for item {line_item_name}",
                    details={
                        "serial_number": line_id,
                        "item_name": line_item_name,
                        "qty":amt,
                    }
                )
                logger.info("Invoice lines updated.")
                QMessageBox.information(dialog, "Success", f"Invoice line {line_id} pending amount updated.")
            except mysql.connector.Error as db_err:
                logger.error(f"MySQL Error: {db_err}")
                QMessageBox.critical(dialog, "MySQL Error", f"Database error: {db_err}")
                log_audit_action(
                    user=getattr(self, 'current_user', None),
                    action_type="ERROR",
                    entity="InvoiceLine",
                    entity_id=None,
                    description=f"Error update pending amount in invoice_line: {str(db_err)}",
                    details={"traceback": traceback.format_exc()}
                )
            except Exception as e:
                logger.error(f"Loging error: {e}")
                QMessageBox.critical(dialog,"Loging Error", f"Could not update log : {e}")
            finally:
                cursor.close()
                conn.close()
            dialog.accept()
            self.refresh_invoice_table()
            self.refresh_stitching_lines_table()


        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(submit)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()


    def open_stitching_record_dialog(self):
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection Error", "Please select one or more fabric invoice lines to create a stitching record.")
            return
        # Fetch selected lines' data
        conn = get_db_connection()
        lines = []
        for row in selected_rows:
            invoice_number_full = self.invoice_table.item(row.row(), 2).text()
            # Strip line number suffix if present
            invoice_number = invoice_number_full.split('-')[0] if '-' in invoice_number_full else invoice_number_full
            item_code = self.invoice_table.item(row.row(), 4).text()
            color = self.invoice_table.item(row.row(), 5).text()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT l.*, i.invoice_number, i.invoice_date, c.short_name FROM invoice_lines l JOIN invoices i ON l.invoice_id = i.id JOIN customers c ON i.customer_id = c.id WHERE i.invoice_number=%s AND l.item_name=%s AND l.color=%s LIMIT 1
            """, (invoice_number_full, item_code, color))
            rowdata = cursor.fetchone()
            cursor.close()
            if rowdata:
                lines.append(rowdata)
        conn.close()
        if not lines:
            QMessageBox.critical(self, "Error", "Could not fetch selected invoice lines.")
            return
        # Dialog window
        from PyQt6.QtWidgets import QFormLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QDialogButtonBox, QLabel, QPushButton, QGroupBox, QComboBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Stitching Record")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enter yardage consumed for each selected fabric line:"))
        consumed_vars = []
        for idx, line in enumerate(lines):
            hbox = QHBoxLayout()
            pending = (line.get('yards_sent') or line.get('quantity', 0) or 0) - (line.get('yards_consumed') or 0)
            hbox.addWidget(QLabel(f"Invoice #{line['invoice_number']} | Item: {line['item_name']} | Pending: {pending} yards"))
            var = QDoubleSpinBox()
            var.setRange(0, pending)
            var.setDecimals(2)
            var.setValue(0)
            hbox.addWidget(var)
            consumed_vars.append(var)
            layout.addLayout(hbox)
        # Stitched item and per-size fields
        form = QFormLayout()
        stitched_item_var = QLineEdit()
        form.addRow("Stitched Item:", stitched_item_var)
        size_labels = ["S", "M", "L", "XL", "XXL", "XXXL"]
        size_vars = {}
        for sz in size_labels:
            v = QSpinBox()
            v.setRange(0, 9999)
            
            font = QFont("Arial", 10)
            font.setItalic(True)
            font.setBold(True)

            # Apply the font to the QSpinBox
            v.setFont(font)

            
            form.addRow(f"Size {sz}:", v)
            size_vars[sz] = v
            
            

            
            
        price_var = QDoubleSpinBox()
        price_var.setRange(0, 999999)
        price_var.setDecimals(2)
        form.addRow("Price:", price_var)
        
        # VAT Toggle
        vat_checkbox = QCheckBox("Add VAT 7%")
        vat_checkbox.setChecked(True)
        vat_checkbox.setToolTip("Check this to add 7% VAT on top of the price")
        form.addRow("VAT:", vat_checkbox)
        
        total_label = QLabel("0.00")
        form.addRow("Total Value:", total_label)
        layout.addLayout(form)
        
        # Add lining fabrics section
        lining_section = QGroupBox("Lining Fabrics (Stitcher-Purchased)")
        lining_layout = QVBoxLayout(lining_section)
        
        # Lining fabrics table
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        lining_table = QTableWidget(0, 4)
        lining_table.setHorizontalHeaderLabels(["Lining Name", "Consumption (yards)", "Unit Price (THB)", "Total Cost"])
        lining_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lining_layout.addWidget(lining_table)
        
        # Lining fabric controls
        lining_controls = QHBoxLayout()
        lining_name_var = QLineEdit()
        lining_name_var.setPlaceholderText("Lining Name")
        lining_consumption_var = QDoubleSpinBox()
        lining_consumption_var.setRange(0, 999.99)
        lining_consumption_var.setDecimals(2)
        lining_consumption_var.setSuffix(" yards")
        lining_unit_price_var = QDoubleSpinBox()
        lining_unit_price_var.setRange(0, 999999.99)
        lining_unit_price_var.setDecimals(2)
        lining_unit_price_var.setSuffix(" THB")
        
        def add_lining_fabric():
            name = lining_name_var.text().strip()
            consumption = lining_consumption_var.value()
            unit_price = lining_unit_price_var.value()
            
            if not name:
                QMessageBox.warning(dialog, "Validation", "Please enter a lining name.")
                return
            if consumption <= 0:
                QMessageBox.warning(dialog, "Validation", "Consumption must be greater than 0.")
                return
            if unit_price <= 0:
                QMessageBox.warning(dialog, "Validation", "Unit price must be greater than 0.")
                return
            
            total_cost = consumption * unit_price
            row = lining_table.rowCount()
            lining_table.insertRow(row)
            lining_table.setItem(row, 0, QTableWidgetItem(name))
            lining_table.setItem(row, 1, QTableWidgetItem(f"{consumption:.2f}"))
            lining_table.setItem(row, 2, QTableWidgetItem(f"{unit_price:.2f}"))
            lining_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
            
            # Clear inputs
            lining_name_var.clear()
            lining_consumption_var.setValue(0)
            lining_unit_price_var.setValue(0)
        
        def remove_lining_fabric():
            current_row = lining_table.currentRow()
            if current_row >= 0:
                lining_table.removeRow(current_row)
        
        add_lining_btn = QPushButton("Add Lining")
        add_lining_btn.clicked.connect(add_lining_fabric)
        remove_lining_btn = QPushButton("Remove Selected")
        remove_lining_btn.clicked.connect(remove_lining_fabric)
        
        lining_controls.addWidget(QLabel("Name:"))
        lining_controls.addWidget(lining_name_var)
        lining_controls.addWidget(QLabel("Consumption:"))
        lining_controls.addWidget(lining_consumption_var)
        lining_controls.addWidget(QLabel("Unit Price:"))
        lining_controls.addWidget(lining_unit_price_var)
        lining_controls.addWidget(add_lining_btn)
        lining_controls.addWidget(remove_lining_btn)
        lining_layout.addLayout(lining_controls)
        
        layout.addWidget(lining_section)
        
        # Add multi-fabric selection section
        multi_fabric_section = QGroupBox("Multi-Fabric Selection (Beta Weaving Fabrics)")
        multi_fabric_layout = QVBoxLayout(multi_fabric_section)
        
        # Multi-fabric table
        multi_fabric_table = QTableWidget(0, 5)
        multi_fabric_table.setHorizontalHeaderLabels(["Fabric Name", "Color", "Invoice", "Consumption (yards)", "Unit Price (THB)"])
        multi_fabric_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        multi_fabric_layout.addWidget(multi_fabric_table)
        
        # Multi-fabric controls with improved selection
        multi_fabric_controls = QHBoxLayout()
        
        def remove_multi_fabric():
            current_row = multi_fabric_table.currentRow()
            if current_row >= 0:
                multi_fabric_table.removeRow(current_row)
        
        # Add fabric button that opens selection dialog
        add_fabric_btn = QPushButton("Add Fabric")
        add_fabric_btn.clicked.connect(lambda: self.open_fabric_selection_dialog(multi_fabric_table))
        remove_multi_fabric_btn = QPushButton("Remove Selected")
        remove_multi_fabric_btn.clicked.connect(remove_multi_fabric)
        
        multi_fabric_controls.addWidget(add_fabric_btn)
        multi_fabric_controls.addWidget(remove_multi_fabric_btn)
        multi_fabric_layout.addLayout(multi_fabric_controls)
        
        layout.addWidget(multi_fabric_section)
        
        # Auto-calculate total value
        def update_total():
            try:
                price = price_var.value()
                total_qty = sum(size_vars[sz].value() for sz in size_labels)
                base_total = price * total_qty
                
                # Add VAT on top if checkbox is checked
                if vat_checkbox.isChecked():
                    vat_amount = base_total * 0.07
                    total = base_total + vat_amount
                else:
                    total = base_total
                
                total_label.setText(f"{total:.2f}")
            except Exception:
                total_label.setText("0.00")
        price_var.valueChanged.connect(update_total)
        for v in size_vars.values():
            v.valueChanged.connect(update_total)
        update_total()
        # Image upload
        image_path = [None]  # Use list for mutability in closure
        image_label = QLabel()
        image_label.setFixedSize(120, 120)
        image_label.setStyleSheet("border: 1px solid #444; background: #222;")
        def upload_image():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "Select Garment Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
            if file_path:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(120, 120, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                    image_label.setPixmap(pixmap)
                    image_path[0] = file_path
        upload_btn = QPushButton("Upload Image")
        upload_btn.clicked.connect(upload_image)
        img_hbox = QHBoxLayout()
        img_hbox.addWidget(upload_btn)
        img_hbox.addWidget(image_label)
        layout.addLayout(img_hbox)
        # Submit logic
        def submit():
            try:
                consumed = [v.value() for v in consumed_vars]
                if any(c <= 0 for c in consumed):
                    raise ValueError("Consumption must be positive.")
                for idx, c in enumerate(consumed):
                    yards_sent = lines[idx].get('yards_sent')
                    if yards_sent is None:
                        yards_sent = lines[idx].get('quantity', 0) or 0
                    yards_consumed = lines[idx].get('yards_consumed')
                    if yards_consumed is None:
                        yards_consumed = 0
                    pending = yards_sent - yards_consumed
                    if c > pending:
                        raise ValueError(f"Consumed ({c}) exceeds pending ({pending}) for line {idx+1}.")
                stitched_item = stitched_item_var.text().strip()
                if not stitched_item:
                    raise ValueError("Stitched item required.")
                size_qty = {sz: size_vars[sz].value() for sz in size_labels}
                price = price_var.value()
                total = float(total_label.text())
            except Exception as e:
                QMessageBox.critical(dialog, "Validation Error", str(e))
                return
            # Insert into DB
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                # Generate serial number
                serial_number = self.generate_serial_number("ST")
                # Save image if uploaded
                image_id = None
                if image_path[0]:
                    ext = os.path.splitext(image_path[0])[1].lower()
                    dest_dir = 'images'
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, serial_number.replace('/', '') + ext)
                    shutil.copy(image_path[0], dest_path)
                    # Insert into images table
                    cursor.execute("INSERT INTO images (file_path, uploaded_at) VALUES (%s, %s)", (dest_path, datetime.now()))
                    image_id = cursor.lastrowid
                # Insert stitching record (with image_id if present)
                cursor.execute("INSERT INTO stitching_invoices (stitching_invoice_number, item_name, yard_consumed, stitched_item, size_qty_json, price, total_value, add_vat, created_at, invoice_line_id, image_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (serial_number, lines[0]['item_name'], sum(consumed), stitched_item, str(size_qty), price, total, vat_checkbox.isChecked(), datetime.now(), lines[0]['id'], image_id))
                
                # Get the stitching invoice ID
                stitching_id = cursor.lastrowid
                
                # Insert lining fabrics if any
                lining_total_cost = 0
                for row in range(lining_table.rowCount()):
                    lining_name = lining_table.item(row, 0).text()
                    consumption = float(lining_table.item(row, 1).text())
                    unit_price = float(lining_table.item(row, 2).text())
                    total_cost = float(lining_table.item(row, 3).text())
                    lining_total_cost += total_cost
                    
                    cursor.execute("""
                        INSERT INTO lining_fabrics 
                        (stitching_invoice_id, lining_name, consumption_yards, unit_price, total_cost, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (stitching_id, lining_name, consumption, unit_price, total_cost, datetime.now()))
                
                # Update total_lining_cost in stitching_invoices table
                if lining_total_cost > 0:
                    cursor.execute("UPDATE stitching_invoices SET total_lining_cost = %s WHERE id = %s", 
                                 (lining_total_cost, stitching_id))
                
                # Insert multi-fabric records if any
                multi_fabric_total_cost = 0
                for row in range(multi_fabric_table.rowCount()):
                    fabric_line_id = multi_fabric_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                    consumption = float(multi_fabric_table.item(row, 3).text())
                    unit_price = float(multi_fabric_table.item(row, 4).text())
                    total_fabric_cost = consumption * unit_price
                    multi_fabric_total_cost += total_fabric_cost
                    
                    cursor.execute("""
                        INSERT INTO garment_fabrics 
                        (stitching_invoice_id, fabric_invoice_line_id, consumption_yards, unit_price, total_fabric_cost, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (stitching_id, fabric_line_id, consumption, unit_price, total_fabric_cost, datetime.now()))
                    
                    # Update the invoice line's yards_consumed
                    cursor.execute("UPDATE invoice_lines SET yards_consumed = IFNULL(yards_consumed,0) + %s WHERE id = %s", 
                                 (consumption, fabric_line_id))
                
                # Update total_fabric_cost in stitching_invoices table
                if multi_fabric_total_cost > 0:
                    cursor.execute("UPDATE stitching_invoices SET total_fabric_cost = %s WHERE id = %s", 
                                 (multi_fabric_total_cost, stitching_id))
                # Update fabric invoice lines
                for idx, line in enumerate(lines):
                    cursor.execute("UPDATE invoice_lines SET yards_consumed = IFNULL(yards_consumed,0) + %s WHERE id = %s", (consumed[idx], line['id']))
                conn.commit()
                # Log audit action for stitching record creation
                log_audit_action(
                    user=self.current_user,
                    action_type="CREATE",
                    entity="StitchingRecord",
                    entity_id=serial_number,
                    description=f"Created stitching record {serial_number} for item {lines[0]['item_name']}",
                    details={
                        "serial_number": serial_number,
                        "item_name": lines[0]['item_name'],
                        "size_qty": size_qty,
                        "price": price,
                        "total": total,
                        "image_path": image_path[0]
                    }
                )
                logger.info("Stitching record created and fabric lines updated.")
                QMessageBox.information(dialog, "Success", f"Stitching record {serial_number} created and fabric lines updated.")
            except Exception as e:
                log_audit_action(
                    user=getattr(self, 'current_user', None),
                    action_type="ERROR",
                    entity="StitchingRecord",
                    entity_id=None,
                    description=f"Error creating stitching record: {str(e)}",
                    details={"traceback": traceback.format_exc()}
                )
                logger.error(f"DB error: {e}")
                QMessageBox.critical(dialog, "DB Error", f"Could not create stitching record: {e}")
            finally:
                cursor.close()
                conn.close()
            dialog.accept()
            self.refresh_invoice_table()
            self.refresh_stitching_lines_table()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(submit)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
    # --- Stitching Record Tab Methods ---
    def group_and_bill_from_stitching(self):
        selected_items = self.stitching_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more unbilled stitching records to group and bill.")
            return
        # Only allow unbilled
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        unbilled_ids = []
        for item in selected_items:
            # Only process parent items (stitching records), not child fabrics
            if item.parent() is None:
                stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
                if stitching_id:
                    cursor.execute("SELECT id, billing_group_id FROM stitching_invoices WHERE id=%s", (stitching_id,))
                    rowdata = cursor.fetchone()
                    if rowdata and not rowdata['billing_group_id']:
                        unbilled_ids.append(rowdata['id'])
        if not unbilled_ids:
            QMessageBox.information(self, "No Unbilled", "All selected records are already billed.")
            cursor.close()
            conn.close()
            return
        # Get customer from first selected
        cursor.execute("SELECT i.customer_id FROM stitching_invoices s LEFT JOIN invoice_lines l ON s.item_name = l.item_name LEFT JOIN invoices i ON l.invoice_id = i.id WHERE s.id=%s LIMIT 1", (unbilled_ids[0],))
        rowdata = cursor.fetchone()
        customer_id = rowdata['customer_id'] if rowdata and rowdata['customer_id'] else None
        if not customer_id:
            QMessageBox.critical(self, "Error", "Could not determine customer for selected records.")
            cursor.close()
            conn.close()
            return
        # Generate group number
        group_number = self.generate_serial_number("GB")
        # Create group
        cursor.execute("INSERT INTO stitching_invoice_groups (group_number, customer_id, created_at) VALUES (%s, %s, %s)", (group_number, customer_id, datetime.now()))
        group_id = cursor.lastrowid
        # Link records
        for sid in unbilled_ids:
            cursor.execute("UPDATE stitching_invoices SET billing_group_id=%s WHERE id=%s", (group_id, sid))
            cursor.execute("INSERT INTO stitching_invoice_group_lines (group_id, stitching_invoice_id) VALUES (%s, %s)", (group_id, sid))
        conn.commit()
        cursor.close()
        conn.close()
        # After creating group, generate PDFs in the correct directory
        self.generate_stitching_fee_pdf(group_id, view_after=False, apply_withholding_tax=False)
        self.generate_fabric_used_pdf(group_id, view_after=False)
        QMessageBox.information(self, "Success", f"Created billing group {group_number} and generated PDFs.")
        self.refresh_stitching_lines_table()

    def view_packing_list_pdf(self):
        selected_items = self.stitching_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Select a stitching record to view its packing list PDF.")
            return
        item = selected_items[0]
        # Only process parent items (stitching records), not child fabrics
        if item.parent() is not None:
            QMessageBox.information(self, "No Selection", "Please select a stitching record, not a fabric detail.")
            return
        serial = item.text(1)  # Serial # is col 1
        serial_filename = serial.replace('/', '')
        dir_path = os.path.join('packing_lists', serial)
        pdf_pattern = os.path.join(dir_path, f'ST*.pdf')
        pdf_files = glob.glob(pdf_pattern)
        if not pdf_files:
            QMessageBox.critical(self, "Packing List PDF", f"Packing List PDF not found: {pdf_pattern}")
            return
        self.open_pdf_system(pdf_files[0])

    def open_pdf_system(self, filepath):
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', filepath])
            elif os.name == 'nt':
                os.startfile(filepath)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', filepath])
            else:
                QMessageBox.information(self, "Open PDF", f"PDF saved at {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Could not open PDF: {e}")

    def has_multi_fabric_or_lining(self, stitching_id):
        """Check if a stitching invoice has multi-fabric or lining fabrics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for multi-fabric records
        cursor.execute("SELECT COUNT(*) FROM garment_fabrics WHERE stitching_invoice_id = %s", (stitching_id,))
        multi_fabric_count = cursor.fetchone()[0]
        
        # Check for lining fabrics
        cursor.execute("SELECT COUNT(*) FROM lining_fabrics WHERE stitching_invoice_id = %s", (stitching_id,))
        lining_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return multi_fabric_count > 0 or lining_count > 0

    def open_fabric_selection_dialog(self, target_table):
        """Open a dialog to select fabrics with search and filtering capabilities"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QDoubleSpinBox, QDialogButtonBox, QComboBox
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Fabric")
        dialog.setMinimumSize(800, 600)
        layout = QVBoxLayout(dialog)
        
        # Add explanation label
        explanation_label = QLabel("Note: Fabrics are listed by date (newest first). Each invoice line has its own pending amount and unit price.")
        explanation_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(explanation_label)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        
        # Search by fabric name
        search_label = QLabel("Search Fabric:")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter fabric name...")
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(search_input)
        
        # Filter by color
        color_label = QLabel("Color:")
        color_combo = QComboBox()
        color_combo.addItem("All Colors")
        filter_layout.addWidget(color_label)
        filter_layout.addWidget(color_combo)
        
        # Filter by customer
        customer_label = QLabel("Customer:")
        customer_combo = QComboBox()
        customer_combo.addItem("All Customers")
        filter_layout.addWidget(customer_label)
        filter_layout.addWidget(customer_combo)
        
        # Filter by invoice
        invoice_label = QLabel("Invoice:")
        invoice_combo = QComboBox()
        invoice_combo.addItem("All Invoices")
        filter_layout.addWidget(invoice_label)
        filter_layout.addWidget(invoice_combo)
        
        layout.addLayout(filter_layout)
        
        # Fabric table
        fabric_table = QTableWidget(0, 8)
        fabric_table.setHorizontalHeaderLabels(["Fabric Name", "Color", "Customer", "Date", "Invoice #", "Pending Yards", "Unit Price", "Select"])
        fabric_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(fabric_table)
        
        # Consumption input
        consumption_layout = QHBoxLayout()
        consumption_label = QLabel("Consumption (yards):")
        consumption_input = QDoubleSpinBox()
        consumption_input.setRange(0, 999.99)
        consumption_input.setDecimals(2)
        consumption_input.setSuffix(" yards")
        consumption_layout.addWidget(consumption_label)
        consumption_layout.addWidget(consumption_input)
        layout.addLayout(consumption_layout)
        
        # Load available fabrics
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.id, l.item_name, l.color, i.invoice_number, 
                   (l.yards_sent - COALESCE(l.yards_consumed, 0)) as pending_yards,
                   l.unit_price, l.id as batch_id, i.invoice_date, c.short_name as customer_name
            FROM invoice_lines l
            JOIN invoices i ON l.invoice_id = i.id
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE (l.yards_sent - COALESCE(l.yards_consumed, 0)) > 0
            ORDER BY i.invoice_date DESC, l.item_name, l.color, i.invoice_number, l.id
        """)
        all_fabrics = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Populate filter dropdowns
        colors = sorted(list(set(f['color'] for f in all_fabrics)))
        customers = sorted(list(set(f['customer_name'] for f in all_fabrics if f['customer_name'])))
        invoices = sorted(list(set(f['invoice_number'] for f in all_fabrics)))
        
        for color in colors:
            color_combo.addItem(color)
        for customer in customers:
            customer_combo.addItem(customer)
        for invoice in invoices:
            invoice_combo.addItem(invoice)
        
        def refresh_fabric_table():
            fabric_table.setRowCount(0)
            search_text = search_input.text().lower()
            selected_color = color_combo.currentText()
            selected_customer = customer_combo.currentText()
            selected_invoice = invoice_combo.currentText()
            
            for fabric in all_fabrics:
                # Apply filters
                if search_text and search_text not in fabric['item_name'].lower():
                    continue
                if selected_color != "All Colors" and fabric['color'] != selected_color:
                    continue
                if selected_customer != "All Customers" and fabric['customer_name'] != selected_customer:
                    continue
                if selected_invoice != "All Invoices" and fabric['invoice_number'] != selected_invoice:
                    continue
                
                # Check if already in target table (check by batch_id to avoid duplicates)
                already_selected = False
                for row in range(target_table.rowCount()):
                    target_fabric_id = target_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                    if target_fabric_id == fabric['id']:
                        already_selected = True
                        break
                
                if already_selected:
                    continue
                
                row = fabric_table.rowCount()
                fabric_table.insertRow(row)
                fabric_table.setItem(row, 0, QTableWidgetItem(fabric['item_name']))
                fabric_table.setItem(row, 1, QTableWidgetItem(fabric['color']))
                fabric_table.setItem(row, 2, QTableWidgetItem(fabric['customer_name'] or ''))
                fabric_table.setItem(row, 3, QTableWidgetItem(format_ddmmyy(fabric['invoice_date']) if fabric['invoice_date'] else ''))
                fabric_table.setItem(row, 4, QTableWidgetItem(fabric['invoice_number']))
                fabric_table.setItem(row, 5, QTableWidgetItem(f"{fabric['pending_yards']:.2f}"))
                fabric_table.setItem(row, 6, QTableWidgetItem(f"{fabric['unit_price']:.2f}"))
                
                # Add checkbox for selection
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                fabric_table.setItem(row, 7, checkbox)
                
                # Store fabric data
                fabric_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, fabric)
        
        # Connect filter controls
        search_input.textChanged.connect(refresh_fabric_table)
        color_combo.currentTextChanged.connect(refresh_fabric_table)
        customer_combo.currentTextChanged.connect(refresh_fabric_table)
        invoice_combo.currentTextChanged.connect(refresh_fabric_table)
        
        # Initial load
        refresh_fabric_table()
        
        # Add selected fabrics to target table
        def add_selected_fabrics():
            consumption = consumption_input.value()
            if consumption <= 0:
                QMessageBox.warning(dialog, "Validation", "Please enter a consumption amount.")
                return
            
            added_count = 0
            for row in range(fabric_table.rowCount()):
                checkbox = fabric_table.item(row, 7)
                if checkbox.checkState() == Qt.CheckState.Checked:
                    fabric = fabric_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                    pending_yards = fabric['pending_yards']
                    
                    if consumption > pending_yards:
                        QMessageBox.warning(dialog, "Validation", 
                                          f"Consumption ({consumption}) exceeds pending yards ({pending_yards}) for {fabric['item_name']}.")
                        continue
                    
                    # Add to target table
                    target_row = target_table.rowCount()
                    target_table.insertRow(target_row)
                    target_table.setItem(target_row, 0, QTableWidgetItem(fabric['item_name']))
                    target_table.setItem(target_row, 1, QTableWidgetItem(fabric['color']))
                    target_table.setItem(target_row, 2, QTableWidgetItem(fabric['invoice_number']))
                    target_table.setItem(target_row, 3, QTableWidgetItem(f"{consumption:.2f}"))
                    target_table.setItem(target_row, 4, QTableWidgetItem(f"{fabric['unit_price']:.2f}"))
                    
                    # Store fabric line ID for database reference
                    target_table.item(target_row, 0).setData(Qt.ItemDataRole.UserRole, fabric['id'])
                    
                    added_count += 1
            
            if added_count > 0:
                QMessageBox.information(dialog, "Success", f"Added {added_count} fabric(s) to the selection.")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "No Selection", "Please select at least one fabric.")
        
        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Selected")
        add_btn.clicked.connect(add_selected_fabrics)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec()

    def generate_stitching_fee_pdf(self, group_id, view_after=False, comments=None, show_success_dialog=False, apply_withholding_tax=False):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT g.group_number, c.short_name as customer, g.created_at, g.invoice_date, g.stitching_comments
            FROM stitching_invoice_groups g
            LEFT JOIN customers c ON g.customer_id = c.id
            WHERE g.id=%s
        ''', (group_id,))
        group = cursor.fetchone()
        if group is None:
            cursor.close()
            conn.close()
            QMessageBox.critical(self, "Error", "Could not find group for PDF generation.")
            return
        comments = str(group.get('stitching_comments', ''))
        cursor.execute('''
            SELECT s.*, l.color, i.invoice_number, i.invoice_date, l.item_name as fabric_name,
                   pl.packing_list_serial, pl.created_at as pl_created_at, pl.tax_invoice_number as pl_tax_invoice_number
            FROM stitching_invoice_group_lines gl
            JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id
            LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
            LEFT JOIN invoices i ON l.invoice_id = i.id
            LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id
            LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE gl.group_id=%s
            ORDER BY pl.tax_invoice_number, pl.packing_list_serial, s.created_at
        ''', (group_id,))
        lines = cursor.fetchall()
        
        # Fetch lining fabrics for all stitching invoices in this group
        stitching_ids = [line['id'] for line in lines]
        lining_fabrics = []
        if stitching_ids:
            format_ids = ','.join(['%s']*len(stitching_ids))
            cursor.execute(f'''
                SELECT lf.*, s.stitching_invoice_number, pl.packing_list_serial
                FROM lining_fabrics lf
                JOIN stitching_invoices s ON lf.stitching_invoice_id = s.id
                LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id
                LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
                WHERE lf.stitching_invoice_id IN ({format_ids})
                ORDER BY pl.packing_list_serial, s.stitching_invoice_number
            ''', tuple(stitching_ids))
            lining_fabrics = cursor.fetchall()
        # Group by packing list's tax_invoice_number
        tax_groups = {}
        for line in lines:
            tax_inv = line.get('pl_tax_invoice_number', None)
            if tax_inv not in tax_groups:
                tax_groups[tax_inv] = []
            tax_groups[tax_inv].append(line)
        # Fetch image paths for all image_ids
        image_map = {}
        image_ids = [line['image_id'] for line in lines if line.get('image_id')]
        if image_ids:
            format_ids = ','.join(['%s']*len(image_ids))
            cursor2 = conn.cursor(dictionary=True)
            cursor2.execute(f"SELECT id, file_path FROM images WHERE id IN ({format_ids})", tuple(image_ids))
            for row in cursor2.fetchall():
                image_map[row['id']] = row['file_path']
            cursor2.close()
        cursor.close()
        conn.close()
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        group_total = 0
        # --- Print header only once ---
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 8, "M.S.K Textile Trading   |   Stitching Invoice", ln=1, align='C')
        pdf.set_font("Arial", '', 9)
        # Use invoice_date if available, otherwise fall back to created_at
        display_date = group.get('invoice_date') or group['created_at']
        group_info = f"Group: {group['group_number']}   Customer: {group['customer']}   Date: {format_ddmmyy(display_date)}"
        pdf.cell(0, 7, group_info, ln=1, align='C')
        pdf.ln(1)
        # Comments Section (like fabric invoice)
        if comments:
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Comments:", ln=1)
            pdf.set_font("Arial", '', 9)
            # Wrap comments to fit page width
            comment_lines = []
            words = comments.split()
            current_line = ""
            for word in words:
                if pdf.get_string_width(current_line + " " + word) < 180:  # Page width minus margins
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        comment_lines.append(current_line)
                    current_line = word
            if current_line:
                comment_lines.append(current_line)
            for line in comment_lines:
                pdf.cell(0, 5, line, ln=1)
        pdf.ln(1)
        
        # Add stitching items section header
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "--- STITCHING ITEMS ---", ln=1)
        
        grand_total = 0
        # Print all tax groups, with a subheading for each tax invoice #
        for tax_inv, group_lines in tax_groups.items():
            pdf.set_font("Arial", 'B', 8)
            pdf.cell(0, 6, f"Tax Invoice #: {tax_inv if tax_inv else '(None)'}", ln=1)
            pdf.set_font("Arial", '', 7)
            # Group by packing list
            pl_groups = {}
            for line in group_lines:
                pl_key = (line.get('packing_list_serial', ''), line.get('pl_created_at'))
                if pl_key not in pl_groups:
                    pl_groups[pl_key] = []
                pl_groups[pl_key].append(line)
            for (pl_serial, pl_created_at), pl_lines in pl_groups.items():
                # Sub-header for each packing list group
                pdf.set_font("Arial", 'B', 7)
                pl_date = format_ddmmyy(pl_created_at) if pl_created_at else ''
                # --- CHANGED: Header order and format ---
                pdf.cell(0, 5, f"Tax Invoice #: {tax_inv if tax_inv else '(None)'}    Packing List #: {pl_serial}    Delivery Date: {pl_date}", ln=1)
                # Table header before each packing list group
                pdf.set_font("Arial", 'B', 8)
                col_widths = [20, 18, 28, 32, 18, 14, 16, 20]  # Serial, Img, Garment, Fabric, Color, Tot, Price, Value
                pdf.cell(col_widths[0], 6, "Serial", 1)
                pdf.cell(col_widths[1], 6, "Img", 1)
                pdf.cell(col_widths[2], 6, "Garment", 1)
                pdf.cell(col_widths[3], 6, "Fabric", 1)
                pdf.cell(col_widths[4], 6, "Color", 1)
                pdf.cell(col_widths[5], 6, "Tot", 1)
                pdf.cell(col_widths[6], 6, "Price", 1)
                pdf.cell(col_widths[7], 6, "Value", 1)
                pdf.ln()
                pdf.set_font("Arial", '', 7)
                pl_total = 0
                for line in pl_lines:
                    pdf.cell(col_widths[0], 18, str(line['stitching_invoice_number'] or ''), 1)
                    # Image cell (now 18x18)
                    img_path = image_map.get(line.get('image_id'))
                    x = pdf.get_x()
                    y = pdf.get_y()
                    if img_path and os.path.exists(img_path):
                        pdf.cell(col_widths[1], 18, '', 1)
                        pdf.image(img_path, x+1, y+1, col_widths[1]-2, 16)
                    else:
                        pdf.cell(col_widths[1], 18, '', 1)
                    pdf.set_xy(x+col_widths[1], y)
                    pdf.cell(col_widths[2], 18, str(line['stitched_item'] or ''), 1)
                    pdf.cell(col_widths[3], 18, str(line['fabric_name'] or ''), 1)
                    pdf.cell(col_widths[4], 18, str(line['color'] or ''), 1)
                    try:
                        size_qty = eval(line['size_qty_json']) if line['size_qty_json'] else {}
                    except Exception:
                        size_qty = {}
                    total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                    pdf.cell(col_widths[5], 18, str(total_qty), 1)
                    # Calculate VAT-inclusive price for display
                    base_price = float(line['price'] or 0)
                    add_vat = line.get('add_vat', False)
                    if add_vat:
                        vat_amount = base_price * 0.07
                        vat_inclusive_price = base_price + vat_amount
                    else:
                        vat_inclusive_price = base_price
                    pdf.cell(col_widths[6], 18, f"{vat_inclusive_price:,.2f}", 1)
                    value = float(line['total_value'] or 0)
                    pdf.cell(col_widths[7], 18, f"{value:,.2f}", 1)
                    pl_total += value
                    pdf.ln(18)
                pdf.set_font("Arial", 'B', 7)
                # --- CHANGED: Total line to be by Tax Invoice ---
                pdf.cell(0, 6, f"Total for Tax Invoice {tax_inv if tax_inv else '(None)'}: {pl_total:,.2f} THB", ln=1)
                pdf.set_font("Arial", '', 7)
                pdf.ln(2)
                grand_total += pl_total
        
        # Calculate stitching totals (with VAT and withholding tax) - MOVED HERE
        stitching_vat_total = 0
        stitching_base_total = 0
        for line in lines:
            if line.get('add_vat'):
                # If VAT was added, calculate the base amount
                total_value = float(line['total_value'] or 0)
                base_amount = total_value / 1.07
                vat_amount = total_value - base_amount
                stitching_vat_total += vat_amount
                stitching_base_total += base_amount
            else:
                # If no VAT, add to base total
                stitching_base_total += float(line['total_value'] or 0)
        
        # Calculate withholding tax for stitching only
        stitching_withholding_tax = 0
        if apply_withholding_tax:
            stitching_withholding_tax = stitching_base_total * 0.03  # 3% of stitching subtotal
        
        # Calculate stitching grand total
        stitching_grand_total = grand_total - stitching_withholding_tax
        
        # Show stitching breakdown - MOVED HERE
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(0, 6, f"Stitching Invoice Sub Total: {stitching_base_total:,.2f} THB", ln=1)
        
        if stitching_vat_total > 0:
            pdf.cell(0, 6, f"VAT 7%: {stitching_vat_total:,.2f} THB", ln=1)
        
        if apply_withholding_tax:
            pdf.cell(0, 6, f"Withholding Tax 3%: {stitching_withholding_tax:,.2f} THB", ln=1)
        
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(0, 6, f"Stitching Invoice Total: {stitching_grand_total:,.2f} THB", ln=1)
        
        # Add lining fabrics section if there are any
        if lining_fabrics:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, "--- LINING FABRICS ---", ln=1)
            
            # Lining fabrics table header
            pdf.set_font("Arial", 'B', 8)
            col_widths = [25, 35, 25, 25, 25]  # Serial, Lining Name, Consumption, Unit Price, Total Cost
            pdf.cell(col_widths[0], 6, "Serial", 1)
            pdf.cell(col_widths[1], 6, "Lining Name", 1)
            pdf.cell(col_widths[2], 6, "Consumption", 1)
            pdf.cell(col_widths[3], 6, "Unit Price", 1)
            pdf.cell(col_widths[4], 6, "Total Cost", 1)
            pdf.ln()
            
            # Lining fabrics table content
            pdf.set_font("Arial", '', 7)
            for lf in lining_fabrics:
                pdf.cell(col_widths[0], 12, str(lf.get('stitching_invoice_number', '')), 1)
                pdf.cell(col_widths[1], 12, str(lf.get('lining_name', '')), 1)
                pdf.cell(col_widths[2], 12, f"{lf.get('consumption_yards', 0):.2f} yards", 1)
                pdf.cell(col_widths[3], 12, f"{lf.get('unit_price', 0):.2f} THB", 1)
                pdf.cell(col_widths[4], 12, f"{lf.get('total_cost', 0):,.2f} THB", 1)
                pdf.ln(12)
        
        # Calculate lining totals (no VAT, no withholding tax)
        lining_total = sum(float(lf.get('total_cost', 0) or 0) for lf in lining_fabrics)
        
        # Show lining breakdown if there are lining fabrics
        if lining_total > 0:
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 8)
            pdf.cell(0, 6, f"Lining Fabric Sub Total: {lining_total:,.2f} THB", ln=1)
            pdf.cell(0, 6, f"VAT 7%: {lining_total * 0.07:,.2f} THB", ln=1)
            lining_grand_total = lining_total * 1.07
            pdf.cell(0, 6, f"Lining Fabric Total: {lining_grand_total:,.2f} THB", ln=1)
        
        # Calculate final total payment due
        if lining_total > 0:
            total_payment_due = stitching_grand_total + lining_grand_total
        else:
            total_payment_due = stitching_grand_total
        
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, f"Total Payment Due: {total_payment_due:,.2f} THB", ln=1)
        safe_group_number = group['group_number'].replace('/', '_')
        dir_path = os.path.join('group_bills', safe_group_number)
        os.makedirs(dir_path, exist_ok=True)
        mm_yy = group['group_number'][3:7] if len(group['group_number']) >= 7 else '0000'
        serial_conn = get_db_connection()
        serial_cursor = serial_conn.cursor()
        serial_cursor.execute("SELECT COUNT(*) FROM stitching_invoice_groups WHERE group_number LIKE %s", (f"GB/{mm_yy}/%",))
        serial = serial_cursor.fetchone()[0]
        serial_cursor.close()
        serial_conn.close()
        pdf_name = f"GB{mm_yy}SI{serial:02d}.pdf"
        out_path = os.path.join(dir_path, pdf_name)
        pdf.output(out_path)
        if view_after:
            self.open_pdf_system(out_path)
        elif show_success_dialog:
            QMessageBox.information(self, "PDF Generated", f"Stitching Invoice PDF saved as {out_path}")

    def generate_fabric_used_pdf(self, group_id, view_after=False, comments=None, show_success_dialog=False):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT g.group_number, c.short_name as customer, g.created_at, g.invoice_date, g.fabric_comments
            FROM stitching_invoice_groups g
            LEFT JOIN customers c ON g.customer_id = c.id
            WHERE g.id=%s
        ''', (group_id,))
        group = cursor.fetchone()
        if group is None:
            cursor.close()
            conn.close()
            QMessageBox.critical(self, "Error", "Could not find group for PDF generation.")
            return
        comments = str(group.get('fabric_comments', ''))
        # Fetch all lines with packing list and invoice info (main fabrics)
        cursor.execute('''
            SELECT l.item_name as fabric_name, l.color, l.delivery_note, l.yards_sent, l.yards_consumed, l.unit_price,
                   i.invoice_number as fabric_invoice_number, i.tax_invoice_number, i.invoice_date, pl.packing_list_serial, pl.created_at as pl_created_at, l.id as invoice_line_id,
                   'main' as fabric_type
            FROM stitching_invoice_group_lines gl
            JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id
            LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
            LEFT JOIN invoices i ON l.invoice_id = i.id
            LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id
            LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE gl.group_id=%s
        ''', (group_id,))
        main_lines = cursor.fetchall()
        
        # Fetch multi-fabric lines
        cursor.execute('''
            SELECT l.item_name as fabric_name, l.color, l.delivery_note, gf.consumption_yards as yards_consumed, gf.unit_price,
                   i.invoice_number as fabric_invoice_number, i.tax_invoice_number, i.invoice_date, pl.packing_list_serial, pl.created_at as pl_created_at, l.id as invoice_line_id,
                   'multi' as fabric_type
            FROM stitching_invoice_group_lines gl
            JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id
            JOIN garment_fabrics gf ON s.id = gf.stitching_invoice_id
            JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
            JOIN invoices i ON l.invoice_id = i.id
            LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id
            LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE gl.group_id=%s
        ''', (group_id,))
        multi_lines = cursor.fetchall()
        
        # Combine main and multi-fabric lines
        lines = main_lines + multi_lines
        cursor.close()
        conn.close()
        # Deduplicate by (invoice_line_id, packing_list_serial, fabric_type)
        unique_lines = []
        seen = set()
        for l in lines:
            key = (l['invoice_line_id'], l['packing_list_serial'], l.get('fabric_type', 'main'))
            if key not in seen:
                seen.add(key)
                unique_lines.append(l)
        # Group by Fabric Tax Invoice #
        tax_groups = defaultdict(list)
        for line in unique_lines:
            key = line.get('tax_invoice_number', '') or '(No Tax Inv)'
            tax_groups[key].append(line)
        # PDF setup
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        # Professional header
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "Beta Weaving Factory Co., Ltd", ln=1, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, "Professional Fabric Supplier", ln=1, align='C')
        pdf.ln(5)
        # Invoice header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"FABRIC INVOICE", ln=1, align='C')
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Group #:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, group['group_number'], 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Date:", 0)
        pdf.set_font("Arial", '', 10)
        # Use invoice_date if available, otherwise fall back to created_at
        display_date = group.get('invoice_date') or group['created_at']
        pdf.cell(50, 6, format_ddmmyy(display_date), ln=1)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Customer:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, group['customer'], ln=1)
        # Comments
        if comments:
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Comments:", ln=1)
            pdf.set_font("Arial", '', 9)
            comment_lines = []
            words = comments.split()
            current_line = ""
            for word in words:
                if pdf.get_string_width(current_line + " " + word) < 180:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        comment_lines.append(current_line)
                    current_line = word
            if current_line:
                comment_lines.append(current_line)
            for line in comment_lines:
                pdf.cell(0, 5, line, ln=1)
        pdf.ln(5)
        # Table columns
        pdf.set_font("Arial", 'B', 8)
        col_widths = [18, 28, 18, 18, 18, 18, 18, 22]  # 8 columns: Img, Fabric Inv #, Fabric Name, Color, Qty, Price, Total, Billed Total
        headers = [
            "Img", "Fabric Inv #", "Fabric Name", "Color", "Qty", "Price", "Total", "Billed Total"
        ]
        grand_total = 0
        for tax_inv, group_lines in tax_groups.items():
            # Find DN # and earliest Delivery Date for this tax group
            dn_numbers = set()
            delivery_dates = []
            for l in group_lines:
                if l.get('delivery_note'):
                    dn_numbers.add(l.get('delivery_note'))
                if l.get('pl_created_at'):
                    delivery_dates.append(l.get('pl_created_at'))
            dn_str = ', '.join(sorted(dn_numbers))
            delivery_date_str = format_ddmmyy(min(delivery_dates)) if delivery_dates else ''
            # Aggregate by (Fabric Name, Color, invoice_line_id) and only use max yards_consumed per invoice_line_id
            sku_map = {}
            max_yards = {}
            for l in group_lines:
                key = (l['fabric_name'], l['color'], l['invoice_line_id'])
                if key not in max_yards or l.get('yards_consumed', 0) > max_yards[key]:
                    max_yards[key] = l.get('yards_consumed', 0)
                    sku_map[key] = {
                        'fabric_inv': l.get('fabric_invoice_number', ''),
                        'fabric_name': l.get('fabric_name', ''),
                        'color': l.get('color', ''),
                        'unit_price': l.get('unit_price', 0) or 0,
                        'billed_total': l.get('yards_consumed', 0) or 0
                    }
            # Now aggregate by (fabric_name, color)
            final_map = {}
            for (fabric_name, color, _), v in sku_map.items():
                key = (fabric_name, color)
                if key not in final_map:
                    final_map[key] = {
                        'fabric_inv': v['fabric_inv'],
                        'fabric_name': v['fabric_name'],
                        'color': v['color'],
                        'qty_billed': 0,
                        'unit_price': v['unit_price'],
                        'total_value': 0,
                        'billed_total': 0
                    }
                final_map[key]['qty_billed'] += v['billed_total']
                final_map[key]['total_value'] += v['billed_total'] * v['unit_price']
                final_map[key]['billed_total'] = v['billed_total']  # For the last line item, but will show per row
            # Sub-header for this tax invoice group
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"Tax Inv #: {tax_inv}    DN #: {dn_str}    Delivery Date: {delivery_date_str}", ln=1)
            # Table header
            pdf.set_font("Arial", 'B', 8)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
            pdf.ln()
            pdf.set_font("Arial", '', 7)
            for (fabric_name, color), sku in final_map.items():
                # Image cell (18x18 for manual insertion)
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.cell(col_widths[0], 18, '', 1)
                pdf.set_xy(x+col_widths[0], y)
                
                pdf.cell(col_widths[1], 18, str(sku['fabric_inv']), 1)
                pdf.cell(col_widths[2], 18, str(fabric_name), 1)
                pdf.cell(col_widths[3], 18, str(color), 1)
                pdf.cell(col_widths[4], 18, format_number(sku['qty_billed']), 1, 0, 'R')
                pdf.cell(col_widths[5], 18, format_number(sku['unit_price']), 1, 0, 'R')
                pdf.cell(col_widths[6], 18, format_number(sku['total_value']), 1, 0, 'R')
                pdf.cell(col_widths[7], 18, format_number(sku['billed_total']), 1, 0, 'R')
                pdf.ln(18)
                grand_total += sku['total_value']
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Total Amount Due: {grand_total:,.2f}", ln=1)
        safe_group_number = group['group_number'].replace('/', '_')
        dir_path = os.path.join('group_bills', safe_group_number)
        os.makedirs(dir_path, exist_ok=True)
        mm_yy = group['group_number'][3:7] if len(group['group_number']) >= 7 else '0000'
        serial_conn = get_db_connection()
        serial_cursor = serial_conn.cursor()
        serial_cursor.execute("SELECT COUNT(*) FROM stitching_invoice_groups WHERE group_number LIKE %s", (f"GB/{mm_yy}/%",))
        serial = serial_cursor.fetchone()[0]
        serial_cursor.close()
        serial_conn.close()
        pdf_name = f"GB{mm_yy}FI{serial:02d}.pdf"
        out_path = os.path.join(dir_path, pdf_name)
        pdf.output(out_path)
        if view_after:
            self.open_pdf_system(out_path)
        elif show_success_dialog:
            QMessageBox.information(self, "PDF Generated", f"Group Fabric Invoice PDF saved as {out_path}")

    def generate_packing_list_pdf(self):
        # Gather filtered rows
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, group_number FROM stitching_invoice_groups")
        group_map = {g['id']: g['group_number'] for g in cursor.fetchall()}
        query = '''
            SELECT
              s.stitching_invoice_number, s.stitched_item, s.item_name, s.image_id,
              (SELECT l.color FROM invoice_lines l WHERE l.item_name = s.item_name LIMIT 1) AS color,
              (SELECT c.short_name FROM customers c JOIN invoices i ON c.id = i.customer_id JOIN invoice_lines l ON l.invoice_id = i.id WHERE l.item_name = s.item_name LIMIT 1) AS customer,
              (SELECT i.invoice_date FROM invoices i JOIN invoice_lines l ON l.invoice_id = i.id WHERE l.item_name = s.item_name LIMIT 1) AS invoice_date,
              s.size_qty_json
            FROM stitching_invoices s
            WHERE 1=1
        '''
        params = []
        if self.filter_fabric_name.currentText():
            query += " AND s.item_name LIKE %s"
            params.append(f"%{self.filter_fabric_name.currentText()}%")
        if self.filter_garment_name.currentText():
            query += " AND s.stitched_item LIKE %s"
            params.append(f"%{self.filter_garment_name.currentText()}%")
        if self.filter_customer_stitch.currentText():
            query += " AND (SELECT c.short_name FROM customers c JOIN invoices i ON c.id = i.customer_id JOIN invoice_lines l ON l.invoice_id = i.id WHERE l.item_name = s.item_name LIMIT 1) LIKE %s"
            params.append(f"%{self.filter_customer_stitch.currentText()}%")
        if self.filter_delivery_date.currentText():
            query += " AND (SELECT i.invoice_date FROM invoices i JOIN invoice_lines l ON l.invoice_id = i.id WHERE l.item_name = s.item_name LIMIT 1) = %s"
            params.append(self.filter_delivery_date.currentText())
        # Apply grouped/non-grouped filter
        if self.show_grouped.isChecked():
            query += " AND s.billing_group_id IS NOT NULL"
        else:
            query += " AND s.billing_group_id IS NULL"
        query += " ORDER BY s.created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Fetch image paths for all image_ids
        image_map = {}
        image_ids = [row['image_id'] for row in rows if row.get('image_id')]
        if image_ids:
            format_ids = ','.join(['%s']*len(image_ids))
            cursor2 = conn.cursor(dictionary=True)
            cursor2.execute(f"SELECT id, file_path FROM images WHERE id IN ({format_ids})", tuple(image_ids))
            for r in cursor2.fetchall():
                image_map[r['id']] = r['file_path']
            cursor2.close()
        cursor.close()
        conn.close()
        for row in rows:
            serial = row['stitching_invoice_number'] or 'unknown_serial'
            # Remove slashes for filename
            serial_filename = serial.replace('/', '')
            # Use MMYY and serial from serial number if possible
            mm_yy = serial_filename[2:6] if len(serial_filename) >= 6 else '0000'
            serial_num = serial_filename[6:] if len(serial_filename) > 6 else '01'
            pdf_name = f"ST{mm_yy}{serial_num}.pdf"
            dir_path = os.path.join('packing_lists', serial)
            os.makedirs(dir_path, exist_ok=True)
            pdf = FPDF('P', 'mm', 'A4')
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 8, "Packing List", ln=1)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, f"Date: {format_ddmmyy(datetime.now())}", ln=1)
            if self.filter_customer_stitch.currentText():
                pdf.cell(0, 7, f"Customer: {self.filter_customer_stitch.currentText()}", ln=1)
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 8)
            pdf.cell(24, 6, "Serial #", 1)
            pdf.cell(18, 6, "Image", 1)
            pdf.cell(28, 6, "Stitched Item", 1)
            pdf.cell(22, 6, "Fabric", 1)
            pdf.cell(14, 6, "Color", 1)
            for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                pdf.cell(8, 6, sz, 1)
            pdf.cell(14, 6, "Total", 1)
            pdf.cell(20, 6, "Delivery", 1)
            pdf.ln()
            pdf.set_font("Arial", '', 8)
            pdf.cell(24, 18, str(row['stitching_invoice_number'] or ''), 1)
            # Image cell
            img_path = image_map.get(row.get('image_id'))
            x = pdf.get_x()
            y = pdf.get_y()
            if img_path and os.path.exists(img_path):
                pdf.cell(18, 18, '', 1)
                pdf.image(img_path, x+1, y+1, 16, 16)
            else:
                pdf.cell(18, 18, '', 1)
            pdf.set_xy(x+18, y)
            pdf.cell(28, 18, str(row['stitched_item'] or ''), 1)
            pdf.cell(22, 18, str(row['item_name'] or ''), 1)
            pdf.cell(14, 18, str(row['color'] or ''), 1)
            try:
                size_qty = eval(row['size_qty_json']) if row['size_qty_json'] else {}
            except Exception:
                size_qty = {}
            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                pdf.cell(8, 18, str(size_qty.get(sz, 0)), 1)
            pdf.cell(14, 18, str(total_qty), 1)
            pdf.cell(20, 18, format_ddmmyy(datetime.now()), 1)
            pdf.ln(18)
            out_path = os.path.join(dir_path, pdf_name)
            pdf.output(out_path)
        QMessageBox.information(self, "Packing List PDF", f"Packing List PDFs saved in 'packing_lists/<serial>/<ST...>.pdf' for each invoice.")

    def on_gb_pdf(self):
        selected_items = self.gb_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Select a group bill to view PDF.")
            return
        item = selected_items[0]
        if item.parent() is None:
            group_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.show_pdf_dialog(group_id)
        else:
            group_item = item.parent()
            group_id = group_item.data(0, Qt.ItemDataRole.UserRole)
            self.show_pdf_dialog(group_id)

    def show_pdf_dialog(self, group_id):
        # List available PDFs for the group
        group_number = None
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT group_number FROM stitching_invoice_groups WHERE id=%s", (group_id,))
        row = cursor.fetchone()
        if row:
            group_number = row['group_number']
        cursor.close()
        conn.close()
        if not group_number:
            QMessageBox.critical(self, "Error", "Could not find group number.")
            return
        mm_yy = group_number[3:7] if len(group_number) >= 7 else '0000'
        safe_group_number = group_number.replace('/', '_')
        group_dir = os.path.join('group_bills', safe_group_number)
        os.makedirs(group_dir, exist_ok=True)

        # Don't regenerate PDFs - just show existing ones
        # PDFs are already generated during group creation with the correct withholding tax setting
        # Now list available PDFs for the group
        stitching_fee_files = glob.glob(os.path.join(group_dir, f'GB{mm_yy}SI*.pdf'))
        fabric_used_files = glob.glob(os.path.join(group_dir, f'GB{mm_yy}FI*.pdf'))
        pdfs = []
        if stitching_fee_files:
            pdfs.append((f"Stitching Invoice", stitching_fee_files[0]))
        if fabric_used_files:
            pdfs.append((f"Group Fabric Invoice", fabric_used_files[0]))
        if not pdfs:
            QMessageBox.information(self, "No PDFs", f"No PDFs found for group {group_number}")
            return
        # Create a simple dialog to show available PDFs
        dialog2 = QDialog(self)
        dialog2.setWindowTitle(f"PDFs for Group {group_number}")
        dialog2.setFixedSize(500, 220)
        layout2 = QVBoxLayout(dialog2)
        layout2.addWidget(QLabel(f"Available PDFs for Group {group_number}"))
        for label, filename in pdfs:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(label))
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, path=filename: self.open_pdf_system(path))
            hbox.addWidget(view_btn)
            saveas_btn = QPushButton("Save As")
            saveas_btn.clicked.connect(lambda checked, path=filename: self.save_pdf_as(path))
            hbox.addWidget(saveas_btn)
            print_btn = QPushButton("Print")
            print_btn.clicked.connect(lambda checked, path=filename: self.print_pdf_system(path))
            hbox.addWidget(print_btn)
            layout2.addLayout(hbox)
        dialog2.setLayout(layout2)
        dialog2.exec()

    def save_pdf_as(self, filepath):
        if not os.path.exists(filepath):
            QMessageBox.critical(self, "Save As", f"PDF file does not exist: {filepath}")
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Save PDF As", os.path.basename(filepath), "PDF files (*.pdf)")
        if dest:
            try:
                shutil.copy(filepath, dest)
                QMessageBox.information(self, "Save As", f"PDF saved to {dest}")
            except Exception as e:
                QMessageBox.critical(self, "Save As", f"Could not save PDF: {e}")

    def print_pdf_system(self, filepath):
        if not os.path.exists(filepath):
            QMessageBox.critical(self, "Print PDF", f"PDF file does not exist: {filepath}")
            return
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', '-a', 'Preview', filepath])
            elif os.name == 'nt':
                os.startfile(filepath, 'print')
            elif os.name == 'posix':
                subprocess.Popen(['lp', filepath])
            else:
                QMessageBox.information(self, "Print PDF", f"PDF saved at {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Print PDF", f"Could not print PDF: {e}")

    def refresh_group_bill_table(self):
        # Clear tree
        self.gb_tree.clear()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = '''SELECT g.id, g.group_number, c.short_name as customer, g.created_at, g.invoice_date, (SELECT COUNT(*) FROM stitching_invoice_group_lines WHERE group_id = g.id) as num_invoices FROM stitching_invoice_groups g LEFT JOIN customers c ON g.customer_id = c.id WHERE 1=1'''
        params = []
        if self.gb_filter_group.currentText():
            query += " AND g.group_number LIKE %s"
            params.append(f"%{self.gb_filter_group.currentText()}%")
        if self.gb_filter_pl.currentText():
            query += " AND EXISTS (SELECT 1 FROM packing_list_lines pll JOIN packing_lists pl ON pll.packing_list_id = pl.id WHERE pl.packing_list_serial LIKE %s AND pll.stitching_invoice_id IN (SELECT stitching_invoice_id FROM stitching_invoice_group_lines WHERE group_id = g.id))"
            params.append(f"%{self.gb_filter_pl.currentText()}%")
        if self.gb_filter_fabric.currentText():
            query += " AND EXISTS (SELECT 1 FROM stitching_invoice_group_lines gl JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id WHERE s.item_name LIKE %s AND gl.group_id = g.id)"
            params.append(f"%{self.gb_filter_fabric.currentText()}%")
        if self.gb_filter_customer.currentText():
            query += " AND c.short_name LIKE %s"
            params.append(f"%{self.gb_filter_customer.currentText()}%")
        if self.gb_filter_taxinv.currentText():
            query += " AND EXISTS (SELECT 1 FROM stitching_invoice_group_lines gl JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id WHERE (i.tax_invoice_number LIKE %s OR s.stitching_invoice_number LIKE %s) AND gl.group_id = g.id)"
            params.append(f"%{self.gb_filter_taxinv.currentText()}%")
            params.append(f"%{self.gb_filter_taxinv.currentText()}%")
        if self.gb_filter_fabinv.currentText():
            query += " AND EXISTS (SELECT 1 FROM stitching_invoice_group_lines gl JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id WHERE i.invoice_number LIKE %s AND gl.group_id = g.id)"
            params.append(f"%{self.gb_filter_fabinv.currentText()}%")
        if self.gb_filter_fabdn.currentText():
            query += " AND EXISTS (SELECT 1 FROM stitching_invoice_group_lines gl JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id WHERE l.delivery_note LIKE %s AND gl.group_id = g.id)"
            params.append(f"%{self.gb_filter_fabdn.currentText()}%")
        date_from = self.gb_filter_date_from.text().strip()
        date_to = self.gb_filter_date_to.text().strip()
        if date_from:
            try:
                if len(date_from) == 8 and date_from.count('/') == 2:
                    day, month, year = date_from.split('/')
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_from_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    query += " AND DATE(g.created_at) >= %s"
                    params.append(date_from_iso)
            except (ValueError, IndexError):
                pass
        if date_to:
            try:
                if len(date_to) == 8 and date_to.count('/') == 2:
                    day, month, year = date_to.split('/')
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_to_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    query += " AND DATE(g.created_at) <= %s"
                    params.append(date_to_iso)
            except (ValueError, IndexError):
                pass
        query += " ORDER BY g.created_at DESC"
        cursor.execute(query, params)
        groups = cursor.fetchall()
        for group in groups:
            parent = QTreeWidgetItem(self.gb_tree)
            parent.setText(0, group['group_number'])
            parent.setText(5, group['customer'] or '')
            # Use invoice_date if available, otherwise fall back to created_at
            display_date = group.get('invoice_date') or group['created_at']
            parent.setText(21, format_ddmmyy(display_date) if display_date else '')
            parent.setText(1, f"Summary ({group['num_invoices']} records)")
            parent.setData(0, Qt.ItemDataRole.UserRole, group['id'])
            
            # Fetch all stitching records for this group with packing list information
            cursor2 = conn.cursor(dictionary=True)
            cursor2.execute('''
                SELECT s.*, l.color, i.tax_invoice_number, i.invoice_number AS fabric_invoice_number, l.delivery_note, 
                       c.short_name as customer, l.unit_price as fabric_unit_price, i.invoice_date,
                       pl.packing_list_serial, pl.created_at as pl_created_at
                FROM stitching_invoice_group_lines gl
                JOIN stitching_invoices s ON gl.stitching_invoice_id = s.id
                LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
                LEFT JOIN invoices i ON l.invoice_id = i.id
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id
                LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
                WHERE gl.group_id = %s
                ORDER BY pl.packing_list_serial, s.created_at DESC
            ''', (group['id'],))
            records = cursor2.fetchall()
            
            # Group records by packing list
            packing_lists = {}
            for rec in records:
                pl_serial = rec.get('packing_list_serial', 'No PL')
                if pl_serial not in packing_lists:
                    packing_lists[pl_serial] = []
                packing_lists[pl_serial].append(rec)
            
            # Calculate totals for the group
            total_fabric_used = 0
            total_fabric_value = 0
            total_stitching_value = 0
            total_items = 0
            size_totals = {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0}
            
            for rec in records:
                yards_consumed = rec.get('yard_consumed', 0) or 0
                fabric_cost = rec.get('fabric_unit_price', 0) or 0
                fabric_value = fabric_cost * yards_consumed
                stitching_value = rec.get('total_value', 0) or 0
                
                total_fabric_used += yards_consumed
                total_fabric_value += fabric_value
                total_stitching_value += stitching_value
                
                try:
                    size_qty = eval(rec.get('size_qty_json', '{}')) if rec.get('size_qty_json') else {}
                except Exception:
                    size_qty = {}
                
                for sz in size_totals:
                    size_totals[sz] += size_qty.get(sz, 0)
                total_items += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            
            # Second level: Fabric Invoice and Stitching Invoice nodes with totals
            fabric_node = QTreeWidgetItem(parent)
            fabric_node.setText(1, "Fabric Invoice")
            fabric_node.setText(9, format_number(total_fabric_used))  # Total Fab Used
            fabric_node.setText(11, format_number(total_fabric_value))  # Total Fab Value
            # Remove sewing quantity details from Fabric Invoice node
            
            stitch_node = QTreeWidgetItem(parent)
            stitch_node.setText(1, "Stitching Invoice")
            stitch_node.setText(20, format_number(total_stitching_value))  # Total Sew Value
            stitch_node.setText(12, format_integer(size_totals["S"]))  # Total S
            stitch_node.setText(13, format_integer(size_totals["M"]))  # Total M
            stitch_node.setText(14, format_integer(size_totals["L"]))  # Total L
            stitch_node.setText(15, format_integer(size_totals["XL"]))  # Total XL
            stitch_node.setText(16, format_integer(size_totals["XXL"]))  # Total XXL
            stitch_node.setText(17, format_integer(size_totals["XXXL"]))  # Total XXXL
            stitch_node.setText(18, format_integer(total_items))  # Total Qty
            
            # Third level: Packing List nodes
            for pl_serial, pl_records in packing_lists.items():
                # Calculate totals for this packing list
                pl_fabric_used = 0
                pl_fabric_value = 0
                pl_stitching_value = 0
                pl_items = 0
                pl_size_totals = {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0}
                pl_created_at = None
                
                for rec in pl_records:
                    yards_consumed = rec.get('yard_consumed', 0) or 0
                    fabric_cost = rec.get('fabric_unit_price', 0) or 0
                    fabric_value = fabric_cost * yards_consumed
                    stitching_value = rec.get('total_value', 0) or 0
                    
                    pl_fabric_used += yards_consumed
                    pl_fabric_value += fabric_value
                    pl_stitching_value += stitching_value
                    
                    if rec.get('pl_created_at'):
                        pl_created_at = rec.get('pl_created_at')
                    
                    try:
                        size_qty = eval(rec.get('size_qty_json', '{}')) if rec.get('size_qty_json') else {}
                    except Exception:
                        size_qty = {}
                    
                    for sz in pl_size_totals:
                        pl_size_totals[sz] += size_qty.get(sz, 0)
                    pl_items += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                
                # Create packing list nodes under both Fabric and Stitching nodes
                pl_fabric_node = QTreeWidgetItem(fabric_node)
                pl_fabric_node.setText(1, f"PL: {pl_serial}")
                pl_fabric_node.setText(9, format_number(pl_fabric_used))  # PL Fab Used
                pl_fabric_node.setText(11, format_number(pl_fabric_value))  # PL Fab Value
                pl_fabric_node.setText(21, format_ddmmyy(pl_created_at) if pl_created_at else '')  # PL Delivery Date
                
                pl_stitch_node = QTreeWidgetItem(stitch_node)
                pl_stitch_node.setText(1, f"PL: {pl_serial}")
                pl_stitch_node.setText(20, format_number(pl_stitching_value))  # PL Sew Value
                pl_stitch_node.setText(12, format_integer(pl_size_totals["S"]))  # PL S
                pl_stitch_node.setText(13, format_integer(pl_size_totals["M"]))  # PL M
                pl_stitch_node.setText(14, format_integer(pl_size_totals["L"]))  # PL L
                pl_stitch_node.setText(15, format_integer(pl_size_totals["XL"]))  # PL XL
                pl_stitch_node.setText(16, format_integer(pl_size_totals["XXL"]))  # PL XXL
                pl_stitch_node.setText(17, format_integer(pl_size_totals["XXXL"]))  # PL XXXL
                pl_stitch_node.setText(18, format_integer(pl_items))  # PL Total Qty
                pl_stitch_node.setText(21, format_ddmmyy(pl_created_at) if pl_created_at else '')  # PL Delivery Date
                
                # Fourth level: Individual records
                for rec in pl_records:
                    # Fabric Invoice details (show only fabric-related information)
                    if rec.get('fabric_invoice_number'):
                        fabric_item = QTreeWidgetItem(pl_fabric_node)
                        fabric_item.setText(0, '')  # Bill # - empty for fabric details
                        fabric_item.setText(1, '')  # PL # - empty for fabric details
                        fabric_item.setText(2, '')  # Garment - empty for fabric details
                        fabric_item.setText(3, rec.get('item_name', ''))  # Fabric
                        fabric_item.setText(4, rec.get('color', ''))  # Color
                        fabric_item.setText(5, rec.get('customer', ''))  # Customer
                        fabric_item.setText(6, rec.get('tax_invoice_number', ''))  # Tax Inv # (Fabric Tax Inv #)
                        fabric_item.setText(7, rec.get('fabric_invoice_number', ''))  # Fabric Inv #
                        fabric_item.setText(8, rec.get('delivery_note', ''))  # Fabric DN
                        yards_consumed = rec.get('yard_consumed', 0) or 0
                        fabric_cost = rec.get('fabric_unit_price', 0) or 0
                        fabric_value = fabric_cost * yards_consumed
                        fabric_item.setText(9, format_number(yards_consumed))  # Fab Used
                        fabric_item.setText(10, format_number(fabric_cost))  # Fab Cost
                        fabric_item.setText(11, format_number(fabric_value))  # Fab Value
                        # Size columns - empty for fabric details
                        fabric_item.setText(12, '')  # S
                        fabric_item.setText(13, '')  # M
                        fabric_item.setText(14, '')  # L
                        fabric_item.setText(15, '')  # XL
                        fabric_item.setText(16, '')  # XXL
                        fabric_item.setText(17, '')  # XXXL
                        fabric_item.setText(18, '')  # Total Qty
                        fabric_item.setText(19, '')  # Sew Cost
                        fabric_item.setText(20, '')  # Sew Value
                        fabric_item.setText(21, format_ddmmyy(rec.get('created_at')) if rec.get('created_at') else '')  # Created At
                    
                    # Stitching Invoice details (show fabric and color, remove tax inv #)
                    stitch_item = QTreeWidgetItem(pl_stitch_node)
                    stitch_item.setText(0, '')  # Bill # - empty for stitching details
                    stitch_item.setText(1, rec.get('packing_list_serial', ''))  # PL #
                    stitch_item.setText(2, rec.get('stitched_item', ''))  # Garment
                    stitch_item.setText(3, rec.get('item_name', ''))  # Fabric
                    stitch_item.setText(4, rec.get('color', ''))  # Color
                    stitch_item.setText(5, rec.get('customer', ''))  # Customer
                    # Tax Inv #: use pl.tax_invoice_number if available, else blank
                    tax_inv = rec.get('pl_tax_invoice_number', '') or ''
                    stitch_item.setText(6, tax_inv)  # Tax Inv # (from packing list)
                    stitch_item.setText(7, '')  # Fabric Inv #
                    stitch_item.setText(8, '')  # Fabric DN
                    stitch_item.setText(9, '')  # Fab Used - empty for stitching details
                    stitch_item.setText(10, '')  # Fab Cost - empty for stitching details
                    stitch_item.setText(11, '')  # Fab Value - empty for stitching details
                    
                    # Size quantities - only for stitching details
                    try:
                        size_qty = eval(rec.get('size_qty_json', '{}')) if rec.get('size_qty_json') else {}
                    except Exception:
                        size_qty = {}
                    stitch_item.setText(12, format_integer(size_qty.get("S", 0)))  # S
                    stitch_item.setText(13, format_integer(size_qty.get("M", 0)))  # M
                    stitch_item.setText(14, format_integer(size_qty.get("L", 0)))  # L
                    stitch_item.setText(15, format_integer(size_qty.get("XL", 0)))  # XL
                    stitch_item.setText(16, format_integer(size_qty.get("XXL", 0)))  # XXL
                    stitch_item.setText(17, format_integer(size_qty.get("XXXL", 0)))  # XXXL
                    total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                    stitch_item.setText(18, format_integer(total_qty))  # Total Qty
                    # Calculate VAT-inclusive price for display
                    base_price = float(rec.get('price', 0) or 0)
                    add_vat = rec.get('add_vat', False)
                    if add_vat:
                        vat_amount = base_price * 0.07
                        vat_inclusive_price = base_price + vat_amount
                    else:
                        vat_inclusive_price = base_price
                    stitch_item.setText(19, format_number(vat_inclusive_price))  # Sew Cost (VAT inclusive)
                    stitch_item.setText(20, format_number(rec.get('total_value', '')))  # Sew Value
                    stitch_item.setText(21, format_ddmmyy(rec.get('created_at')) if rec.get('created_at') else '')  # Created At
            cursor2.close()
        cursor.close()
        conn.close()
        self.populate_gb_filters()

    def populate_gb_filters(self):
        def get_unique_gb_values():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT group_number FROM stitching_invoice_groups ORDER BY group_number DESC")
            groups = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT pl.packing_list_serial FROM packing_list_lines pll JOIN packing_lists pl ON pll.packing_list_id = pl.id ORDER BY pl.packing_list_serial")
            pls = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT s.item_name FROM stitching_invoices s ORDER BY s.item_name")
            fabrics = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT c.short_name FROM stitching_invoice_groups g LEFT JOIN customers c ON g.customer_id = c.id ORDER BY c.short_name")
            customers = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT i.tax_invoice_number FROM invoices i WHERE i.tax_invoice_number IS NOT NULL ORDER BY i.tax_invoice_number")
            taxinvs = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT s.stitching_invoice_number FROM stitching_invoices s ORDER BY s.stitching_invoice_number")
            stitchinvs = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT i.invoice_number FROM invoices i ORDER BY i.invoice_number")
            fabinvs = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT l.delivery_note FROM invoice_lines l WHERE l.delivery_note IS NOT NULL ORDER BY l.delivery_note")
            fabdns = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.close()
            conn.close()
            return groups, pls, fabrics, customers, taxinvs, stitchinvs, fabinvs, fabdns
        groups, pls, fabrics, customers, taxinvs, stitchinvs, fabinvs, fabdns = get_unique_gb_values()
        # Only repopulate if not currently filtering
        if not self.gb_filter_group.currentText():
            self.gb_filter_group.clear()
            self.gb_filter_group.addItem("")
            self.gb_filter_group.addItems(groups)
        if not self.gb_filter_pl.currentText():
            self.gb_filter_pl.clear()
            self.gb_filter_pl.addItem("")
            self.gb_filter_pl.addItems(pls)
        if not self.gb_filter_fabric.currentText():
            self.gb_filter_fabric.clear()
            self.gb_filter_fabric.addItem("")
            self.gb_filter_fabric.addItems(fabrics)
        if not self.gb_filter_customer.currentText():
            self.gb_filter_customer.clear()
            self.gb_filter_customer.addItem("")
            self.gb_filter_customer.addItems(customers)
        if not self.gb_filter_taxinv.currentText():
            self.gb_filter_taxinv.clear()
            self.gb_filter_taxinv.addItem("")
            self.gb_filter_taxinv.addItems(taxinvs + stitchinvs)
        if not self.gb_filter_fabinv.currentText():
            self.gb_filter_fabinv.clear()
            self.gb_filter_fabinv.addItem("")
            self.gb_filter_fabinv.addItems(fabinvs)
        if not self.gb_filter_fabdn.currentText():
            self.gb_filter_fabdn.clear()
            self.gb_filter_fabdn.addItem("")
            self.gb_filter_fabdn.addItems(fabdns)
        # Connect filter changes to debounced update
        self.gb_filter_group.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_pl.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_fabric.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_customer.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_taxinv.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_fabinv.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_fabdn.currentTextChanged.connect(self.trigger_filter_update)
        self.gb_filter_date_from.textChanged.connect(self.trigger_filter_update)
        self.gb_filter_date_to.textChanged.connect(self.trigger_filter_update)

    def init_database(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id VARCHAR(50) UNIQUE,
                short_name VARCHAR(50) UNIQUE,
                full_name VARCHAR(255),
                registration_date DATE,
                is_active BOOLEAN DEFAULT TRUE
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_number VARCHAR(32),
                customer_id INT,
                invoice_date DATE,
                total_amount DECIMAL(12,2),
                status VARCHAR(20),
                tax_invoice_number VARCHAR(32),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )''')
            # Ensure tax_invoice_number column exists
            cursor.execute("SHOW COLUMNS FROM invoices LIKE 'tax_invoice_number'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE invoices ADD COLUMN tax_invoice_number VARCHAR(32)")
            cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_lines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_id INT,
                item_name VARCHAR(100),
                quantity INT,
                unit_price DECIMAL(10,2),
                delivered_location VARCHAR(100),
                is_defective BOOLEAN DEFAULT FALSE,
                color VARCHAR(100),
                delivery_note VARCHAR(100),
                yards_sent DECIMAL(10,2),
                yards_consumed DECIMAL(10,2),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS fabric_inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(100),
                total_delivered DECIMAL(10,2),
                total_consumed DECIMAL(10,2),
                total_defective DECIMAL(10,2),
                pending_amount DECIMAL(10,2)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_path VARCHAR(255),
                uploaded_at DATETIME
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS stitching_invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stitching_invoice_number VARCHAR(32),
                item_name VARCHAR(100),
                yard_consumed DECIMAL(10,2),
                stitched_item VARCHAR(100),
                size_qty_json TEXT,
                price DECIMAL(10,2),
                total_value DECIMAL(12,2),
                add_vat BOOLEAN DEFAULT FALSE,
                image_id INT,
                created_at DATETIME,
                billing_group_id INT,
                invoice_line_id INT,
                total_fabric_cost DECIMAL(12,2) DEFAULT NULL,
                total_lining_cost DECIMAL(12,2) DEFAULT 0,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                level VARCHAR(10),
                message TEXT,
                context TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS stitching_invoice_groups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_number VARCHAR(32),
                customer_id INT,
                created_at DATETIME,
                invoice_date DATE,
                stitching_comments TEXT,
                fabric_comments TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS stitching_invoice_group_lines (
                group_id INT,
                stitching_invoice_id INT,
                PRIMARY KEY (group_id, stitching_invoice_id),
                FOREIGN KEY (group_id) REFERENCES stitching_invoice_groups(id),
                FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id)
            )''')
            
            # New tables for multi-fabric and lining fabrics
            cursor.execute('''CREATE TABLE IF NOT EXISTS garment_fabrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stitching_invoice_id INT,
                fabric_invoice_line_id INT,
                consumption_yards DECIMAL(10,2),
                unit_price DECIMAL(10,2),
                total_fabric_cost DECIMAL(12,2),
                created_at DATETIME,
                FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id),
                FOREIGN KEY (fabric_invoice_line_id) REFERENCES invoice_lines(id)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS lining_fabrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stitching_invoice_id INT,
                lining_name VARCHAR(100),
                consumption_yards DECIMAL(10,2),
                unit_price DECIMAL(10,2),
                total_cost DECIMAL(12,2),
                created_at DATETIME,
                FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id)
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS packing_lists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                packing_list_serial VARCHAR(32) UNIQUE,
                customer_id INT,
                created_at DATETIME,
                delivery_date DATE,
                total_records INT DEFAULT 0,
                total_items INT DEFAULT 0,
                comments TEXT,
                tax_invoice_number VARCHAR(64),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )''')
            # Check if all required columns exist, if not recreate the table
            cursor.execute("SHOW COLUMNS FROM packing_lists")
            existing_columns = [col[0] for col in cursor.fetchall()]
            required_columns = ['id', 'packing_list_serial', 'customer_id', 'created_at', 'total_records', 'total_items']
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            if missing_columns:
                logger.info(f"Missing columns in packing_lists table: {missing_columns}. Recreating table...")
                cursor.execute("DROP TABLE IF EXISTS packing_list_lines")  # Drop dependent table first
                cursor.execute("DROP TABLE IF EXISTS packing_lists")
                cursor.execute('''CREATE TABLE packing_lists (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    packing_list_serial VARCHAR(32) UNIQUE,
                    customer_id INT,
                    created_at DATETIME,
                    total_records INT DEFAULT 0,
                    total_items INT DEFAULT 0,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )''')
                cursor.execute('''CREATE TABLE packing_list_lines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    packing_list_id INT,
                    stitching_invoice_id INT,
                    FOREIGN KEY (packing_list_id) REFERENCES packing_lists(id),
                    FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id)
                )''')
            else:
                # Ensure packing_list_serial column exists
                cursor.execute("SHOW COLUMNS FROM packing_lists LIKE 'packing_list_serial'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE packing_lists ADD COLUMN packing_list_serial VARCHAR(32) UNIQUE")
                # Ensure total_records column exists
                cursor.execute("SHOW COLUMNS FROM packing_lists LIKE 'total_records'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE packing_lists ADD COLUMN total_records INT DEFAULT 0")
                # Ensure total_items column exists
                cursor.execute("SHOW COLUMNS FROM packing_lists LIKE 'total_items'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE packing_lists ADD COLUMN total_items INT DEFAULT 0")
                cursor.execute('''CREATE TABLE IF NOT EXISTS packing_list_lines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    packing_list_id INT,
                    stitching_invoice_id INT,
                    FOREIGN KEY (packing_list_id) REFERENCES packing_lists(id),
                    FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id)
                )''')
                # Ensure all required columns exist in packing_list_lines table
                cursor.execute("SHOW COLUMNS FROM packing_list_lines LIKE 'packing_list_id'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE packing_list_lines ADD COLUMN packing_list_id INT")
                cursor.execute("SHOW COLUMNS FROM packing_list_lines LIKE 'stitching_invoice_id'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE packing_list_lines ADD COLUMN stitching_invoice_id INT")
                # Check for old column name and fix it
                cursor.execute("SHOW COLUMNS FROM packing_list_lines LIKE 'stitching_record_id'")
                if cursor.fetchone():
                    logger.info("Found old stitching_record_id column. Recreating table with correct schema...")
                    cursor.execute("DROP TABLE IF EXISTS packing_list_lines")
                    cursor.execute('''CREATE TABLE packing_list_lines (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        packing_list_id INT,
                        stitching_invoice_id INT,
                        FOREIGN KEY (packing_list_id) REFERENCES packing_lists(id),
                        FOREIGN KEY (stitching_invoice_id) REFERENCES stitching_invoices(id)
                    )''')
            # Create users table if not exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) UNIQUE,
                password_hash VARCHAR(128),
                is_admin BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            # Insert default admin user if not present
            cursor.execute("SELECT id FROM users WHERE username='admin'")
            if not cursor.fetchone():
                admin_hash = hashlib.sha256('admin'.encode('utf-8')).hexdigest()
                cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)", ('admin', admin_hash, True))
                
            # Insert nita user if not present
            cursor.execute("SELECT id FROM users WHERE username='nita'")
            if not cursor.fetchone():
                admin_hash = hashlib.sha256('nitabeta'.encode('utf-8')).hexdigest()
                cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)", ('nita', admin_hash, True))
            
            # Insert james user if not present
            cursor.execute("SELECT id FROM users WHERE username='james'")
            if not cursor.fetchone():
                admin_hash = hashlib.sha256('james3'.encode('utf-8')).hexdigest()
                cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)", ('james', admin_hash, True))
            
            # Insert nut user if not present
            cursor.execute("SELECT id FROM users WHERE username='nut'")
            if not cursor.fetchone():
                admin_hash = hashlib.sha256('nut2'.encode('utf-8')).hexdigest()
                cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, %s)", ('nut', admin_hash, True))
            
            # Create serial_counters table for robust serial generation
            try:
                cursor.execute("CREATE TABLE serial_counters (serial_type VARCHAR(32), last_value INT)")
                cursor.execute("ALTER TABLE serial_counters ADD PRIMARY KEY (serial_type)")
            except:
                # Table might already exist, ignore error
                pass
            # Create audit_logs table for audit trail
            cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user VARCHAR(64),
                action_type VARCHAR(32),
                entity VARCHAR(64),
                entity_id VARCHAR(64),
                description TEXT,
                details TEXT
            )''')
            conn.commit()
        except Error as e:
            logger.error(f"DB init failed: {e}")
            QMessageBox.critical(self, "DB Error", f"Could not initialize database: {e}")
            sys.exit(1)
        finally:
            cursor.close()
            conn.close()

    def on_stitching_item_double_clicked(self, item, column):
        """Handle double-click on stitching tree items"""
        # Check if this is an expandable item (first column with expand indicator)
        if column == 0:
            is_expandable = item.data(column, Qt.ItemDataRole.UserRole + 1)
            if is_expandable:
                # Toggle expand/collapse
                self.toggle_stitching_item_expansion(item)
                return
        
        # Handle regular double-click for editing
        self.on_stitching_double_click(item)
    
    def toggle_stitching_item_expansion(self, item):
        """Toggle expansion of a stitching tree item"""
        # Get the item data
        stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
        current_text = item.text(0)
        
        # Check if currently expanded (has ▼) or collapsed (has ▶)
        is_expanded = "▼" in current_text
        
        if is_expanded:
            # Collapse: hide child items and change to ▶
            self.collapse_stitching_item(item)
            item.setText(0, "▶ " + current_text.replace("▼ ", ""))
        else:
            # Expand: show child items and change to ▼
            self.expand_stitching_item(item, stitching_id)
            item.setText(0, "▼ " + current_text.replace("▶ ", ""))
    
    def expand_stitching_item(self, item, stitching_id):
        """Expand a stitching tree item to show child fabrics"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get multi-fabric details
        cursor.execute("""
            SELECT gf.*, l.item_name, l.color, i.invoice_number
            FROM garment_fabrics gf
            JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
            JOIN invoices i ON l.invoice_id = i.id
            WHERE gf.stitching_invoice_id = %s
            ORDER BY l.item_name, l.color
        """, (stitching_id,))
        multi_fabrics = cursor.fetchall()
        
        # Get lining fabric details
        cursor.execute("""
            SELECT * FROM lining_fabrics 
            WHERE stitching_invoice_id = %s
            ORDER BY lining_name
        """, (stitching_id,))
        lining_fabrics = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Add multi-fabric details
        for fabric in multi_fabrics:
            child_item = QTreeWidgetItem(item)
            
            child_values = [
                "  └─ " + fabric['item_name'],  # Fabric name (indented)
                fabric['color'],  # Color
                fabric['invoice_number'],  # Invoice
                format_number(fabric['consumption_yards']),  # Consumption
                format_number(fabric['unit_price']),  # Unit Price
                format_number(fabric['total_fabric_cost']),  # Total Cost
                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""  # Empty for other columns
            ]
            
            for col_idx, val in enumerate(child_values):
                child_item.setText(col_idx, str(val))
                if col_idx == 0:
                    child_item.setData(col_idx, Qt.ItemDataRole.UserRole, stitching_id)  # Parent ID
                    child_item.setData(col_idx, Qt.ItemDataRole.UserRole + 2, "multi_fabric")  # Type
        
        # Add lining fabric details
        for lining in lining_fabrics:
            child_item = QTreeWidgetItem(item)
            
            child_values = [
                "  └─ " + lining['lining_name'],  # Lining name (indented)
                "",  # Color (empty for lining)
                "",  # Invoice (empty for lining)
                format_number(lining['consumption_yards']),  # Consumption
                format_number(lining['unit_price']),  # Unit Price
                format_number(lining['total_cost']),  # Total Cost
                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""  # Empty for other columns
            ]
            
            for col_idx, val in enumerate(child_values):
                child_item.setText(col_idx, str(val))
                if col_idx == 0:
                    child_item.setData(col_idx, Qt.ItemDataRole.UserRole, stitching_id)  # Parent ID
                    child_item.setData(col_idx, Qt.ItemDataRole.UserRole + 2, "lining")  # Type
    
    def collapse_stitching_item(self, item):
        """Collapse a stitching tree item to hide child fabrics"""
        # Remove all child items
        while item.childCount() > 0:
            item.removeChild(item.child(0))
    
    def on_stitching_double_click(self, item):
        # Get the stitching invoice ID from the item data
        stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
        if stitching_id:
            # Check if this is a grouped record (has billing_group_id)
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT billing_group_id FROM stitching_invoices WHERE id = %s", (stitching_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result['billing_group_id']:
                # This is a grouped record, show PDF dialog
                self.show_pdf_dialog(result['billing_group_id'])
            else:
                # This is not grouped, open edit dialog
                self.open_edit_stitching_dialog(stitching_id)
        else:
            QMessageBox.information(self, "Not Billed", "Selected invoice is not yet billed/grouped.")
    
    def open_edit_stitching_dialog(self, stitching_id):
        """Open dialog to edit an existing stitching record"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch stitching record
        cursor.execute("""
            SELECT s.*, l.item_name as fabric_name, l.color, i.invoice_number
            FROM stitching_invoices s
            LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
            LEFT JOIN invoices i ON l.invoice_id = i.id
            WHERE s.id = %s
        """, (stitching_id,))
        stitching_record = cursor.fetchone()
        
        if not stitching_record:
            cursor.close()
            conn.close()
            QMessageBox.critical(self, "Error", "Could not find stitching record.")
            return
        
        # Fetch lining fabrics
        cursor.execute("SELECT * FROM lining_fabrics WHERE stitching_invoice_id = %s ORDER BY id", (stitching_id,))
        existing_lining_fabrics = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create dialog
        from PyQt6.QtWidgets import QFormLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QDialogButtonBox, QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Stitching Record - {stitching_record['stitching_invoice_number']}")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        # Basic info (read-only)
        info_layout = QFormLayout()
        info_layout.addRow("Serial Number:", QLabel(stitching_record['stitching_invoice_number']))
        info_layout.addRow("Fabric:", QLabel(stitching_record.get('fabric_name', 'N/A')))
        info_layout.addRow("Color:", QLabel(stitching_record.get('color', 'N/A')))
        info_layout.addRow("Invoice:", QLabel(stitching_record.get('invoice_number', 'N/A')))
        layout.addLayout(info_layout)
        
        # Editable fields
        form = QFormLayout()
        stitched_item_var = QLineEdit(stitching_record['stitched_item'])
        form.addRow("Stitched Item:", stitched_item_var)
        
        # Size quantities
        size_labels = ["S", "M", "L", "XL", "XXL", "XXXL"]
        size_vars = {}
        size_qty = eval(stitching_record['size_qty_json']) if stitching_record['size_qty_json'] else {}
        
        for sz in size_labels:
            v = QSpinBox()
            v.setRange(0, 9999)
            v.setValue(size_qty.get(sz, 0))
            form.addRow(f"Size {sz}:", v)
            size_vars[sz] = v
        
        price_var = QDoubleSpinBox()
        price_var.setRange(0, 999999)
        price_var.setDecimals(2)
        price_var.setValue(stitching_record['price'])
        form.addRow("Price:", price_var)
        
        # VAT Toggle
        vat_checkbox = QCheckBox("Add VAT 7%")
        vat_checkbox.setChecked(stitching_record.get('add_vat', False))
        form.addRow("VAT:", vat_checkbox)
        
        total_label = QLabel(f"{stitching_record['total_value']:.2f}")
        form.addRow("Total Value:", total_label)
        layout.addLayout(form)
        
        # Auto-calculate total value
        def update_total():
            try:
                price = price_var.value()
                total_qty = sum(size_vars[sz].value() for sz in size_labels)
                base_total = price * total_qty
                
                if vat_checkbox.isChecked():
                    vat_amount = base_total * 0.07
                    total = base_total + vat_amount
                else:
                    total = base_total
                
                total_label.setText(f"{total:.2f}")
            except Exception:
                total_label.setText("0.00")
        
        price_var.valueChanged.connect(update_total)
        for v in size_vars.values():
            v.valueChanged.connect(update_total)
        vat_checkbox.toggled.connect(update_total)
        update_total()
        
        # Lining fabrics section
        lining_section = QGroupBox("Lining Fabrics (Stitcher-Purchased)")
        lining_layout = QVBoxLayout(lining_section)
        
        lining_table = QTableWidget(0, 4)
        lining_table.setHorizontalHeaderLabels(["Lining Name", "Consumption (yards)", "Unit Price (THB)", "Total Cost"])
        lining_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lining_layout.addWidget(lining_table)
        
        # Load existing lining fabrics
        for lf in existing_lining_fabrics:
            row = lining_table.rowCount()
            lining_table.insertRow(row)
            lining_table.setItem(row, 0, QTableWidgetItem(lf['lining_name']))
            lining_table.setItem(row, 1, QTableWidgetItem(f"{lf['consumption_yards']:.2f}"))
            lining_table.setItem(row, 2, QTableWidgetItem(f"{lf['unit_price']:.2f}"))
            lining_table.setItem(row, 3, QTableWidgetItem(f"{lf['total_cost']:.2f}"))
        
        # Lining fabric controls
        lining_controls = QHBoxLayout()
        lining_name_var = QLineEdit()
        lining_name_var.setPlaceholderText("Lining Name")
        lining_consumption_var = QDoubleSpinBox()
        lining_consumption_var.setRange(0, 999.99)
        lining_consumption_var.setDecimals(2)
        lining_consumption_var.setSuffix(" yards")
        lining_unit_price_var = QDoubleSpinBox()
        lining_unit_price_var.setRange(0, 999999.99)
        lining_unit_price_var.setDecimals(2)
        lining_unit_price_var.setSuffix(" THB")
        
        def add_lining_fabric():
            name = lining_name_var.text().strip()
            consumption = lining_consumption_var.value()
            unit_price = lining_unit_price_var.value()
            
            if not name:
                QMessageBox.warning(dialog, "Validation", "Please enter a lining name.")
                return
            if consumption <= 0:
                QMessageBox.warning(dialog, "Validation", "Consumption must be greater than 0.")
                return
            if unit_price <= 0:
                QMessageBox.warning(dialog, "Validation", "Unit price must be greater than 0.")
                return
            
            total_cost = consumption * unit_price
            row = lining_table.rowCount()
            lining_table.insertRow(row)
            lining_table.setItem(row, 0, QTableWidgetItem(name))
            lining_table.setItem(row, 1, QTableWidgetItem(f"{consumption:.2f}"))
            lining_table.setItem(row, 2, QTableWidgetItem(f"{unit_price:.2f}"))
            lining_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
            
            # Clear inputs
            lining_name_var.clear()
            lining_consumption_var.setValue(0)
            lining_unit_price_var.setValue(0)
        
        def remove_lining_fabric():
            current_row = lining_table.currentRow()
            if current_row >= 0:
                lining_table.removeRow(current_row)
        
        add_lining_btn = QPushButton("Add Lining")
        add_lining_btn.clicked.connect(add_lining_fabric)
        remove_lining_btn = QPushButton("Remove Selected")
        remove_lining_btn.clicked.connect(remove_lining_fabric)
        
        lining_controls.addWidget(QLabel("Name:"))
        lining_controls.addWidget(lining_name_var)
        lining_controls.addWidget(QLabel("Consumption:"))
        lining_controls.addWidget(lining_consumption_var)
        lining_controls.addWidget(QLabel("Unit Price:"))
        lining_controls.addWidget(lining_unit_price_var)
        lining_controls.addWidget(add_lining_btn)
        lining_controls.addWidget(remove_lining_btn)
        lining_layout.addLayout(lining_controls)
        
        layout.addWidget(lining_section)
        
        # Add multi-fabric selection section
        multi_fabric_section = QGroupBox("Multi-Fabric Selection (Beta Weaving Fabrics)")
        multi_fabric_layout = QVBoxLayout(multi_fabric_section)
        
        # Multi-fabric table
        multi_fabric_table = QTableWidget(0, 5)
        multi_fabric_table.setHorizontalHeaderLabels(["Fabric Name", "Color", "Invoice", "Consumption (yards)", "Unit Price (THB)"])
        multi_fabric_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        multi_fabric_layout.addWidget(multi_fabric_table)
        
        # Load existing multi-fabrics
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT gf.*, l.item_name, l.color, i.invoice_number
            FROM garment_fabrics gf
            JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
            JOIN invoices i ON l.invoice_id = i.id
            WHERE gf.stitching_invoice_id = %s
            ORDER BY gf.id
        """, (stitching_id,))
        existing_multi_fabrics = cursor.fetchall()
        
        for mf in existing_multi_fabrics:
            row = multi_fabric_table.rowCount()
            multi_fabric_table.insertRow(row)
            multi_fabric_table.setItem(row, 0, QTableWidgetItem(mf['item_name']))
            multi_fabric_table.setItem(row, 1, QTableWidgetItem(mf['color']))
            multi_fabric_table.setItem(row, 2, QTableWidgetItem(mf['invoice_number']))
            multi_fabric_table.setItem(row, 3, QTableWidgetItem(f"{mf['consumption_yards']:.2f}"))
            multi_fabric_table.setItem(row, 4, QTableWidgetItem(f"{mf['unit_price']:.2f}"))
            
            # Store fabric line ID for database reference
            multi_fabric_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, mf['fabric_invoice_line_id'])
        
        # Multi-fabric controls with improved selection
        multi_fabric_controls = QHBoxLayout()
        
        # Add fabric button that opens selection dialog
        add_fabric_btn = QPushButton("Add Fabric")
        add_fabric_btn.clicked.connect(lambda: self.open_fabric_selection_dialog(multi_fabric_table))
        remove_multi_fabric_btn = QPushButton("Remove Selected")
        remove_multi_fabric_btn.clicked.connect(remove_multi_fabric)
        
        multi_fabric_controls.addWidget(add_fabric_btn)
        multi_fabric_controls.addWidget(remove_multi_fabric_btn)
        multi_fabric_layout.addLayout(multi_fabric_controls)
        
        def remove_multi_fabric():
            current_row = multi_fabric_table.currentRow()
            if current_row >= 0:
                multi_fabric_table.removeRow(current_row)
        
        layout.addWidget(multi_fabric_section)
        
        # Submit function
        def submit():
            try:
                stitched_item = stitched_item_var.text().strip()
                if not stitched_item:
                    raise ValueError("Stitched item required.")
                
                size_qty = {sz: size_vars[sz].value() for sz in size_labels}
                price = price_var.value()
                total = float(total_label.text())
                
            except Exception as e:
                QMessageBox.critical(dialog, "Validation Error", str(e))
                return
            
            # Update database
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                # Update stitching record
                cursor.execute("""
                    UPDATE stitching_invoices 
                    SET stitched_item = %s, size_qty_json = %s, price = %s, total_value = %s, add_vat = %s
                    WHERE id = %s
                """, (stitched_item, str(size_qty), price, total, vat_checkbox.isChecked(), stitching_id))
                
                # Delete existing lining fabrics
                cursor.execute("DELETE FROM lining_fabrics WHERE stitching_invoice_id = %s", (stitching_id,))
                
                # Insert new lining fabrics
                lining_total_cost = 0
                for row in range(lining_table.rowCount()):
                    lining_name = lining_table.item(row, 0).text()
                    consumption = float(lining_table.item(row, 1).text())
                    unit_price = float(lining_table.item(row, 2).text())
                    total_cost = float(lining_table.item(row, 3).text())
                    lining_total_cost += total_cost
                    
                    cursor.execute("""
                        INSERT INTO lining_fabrics 
                        (stitching_invoice_id, lining_name, consumption_yards, unit_price, total_cost, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (stitching_id, lining_name, consumption, unit_price, total_cost, datetime.now()))
                
                # Update total_lining_cost
                cursor.execute("UPDATE stitching_invoices SET total_lining_cost = %s WHERE id = %s", 
                             (lining_total_cost, stitching_id))
                
                # Delete existing multi-fabric records
                cursor.execute("DELETE FROM garment_fabrics WHERE stitching_invoice_id = %s", (stitching_id,))
                
                # Insert new multi-fabric records
                multi_fabric_total_cost = 0
                for row in range(multi_fabric_table.rowCount()):
                    fabric_line_id = multi_fabric_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                    consumption = float(multi_fabric_table.item(row, 3).text())
                    unit_price = float(multi_fabric_table.item(row, 4).text())
                    total_fabric_cost = consumption * unit_price
                    multi_fabric_total_cost += total_fabric_cost
                    
                    cursor.execute("""
                        INSERT INTO garment_fabrics 
                        (stitching_invoice_id, fabric_invoice_line_id, consumption_yards, unit_price, total_fabric_cost, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (stitching_id, fabric_line_id, consumption, unit_price, total_fabric_cost, datetime.now()))
                    
                    # Update the invoice line's yards_consumed
                    cursor.execute("UPDATE invoice_lines SET yards_consumed = IFNULL(yards_consumed,0) + %s WHERE id = %s", 
                                 (consumption, fabric_line_id))
                
                # Update total_fabric_cost
                cursor.execute("UPDATE stitching_invoices SET total_fabric_cost = %s WHERE id = %s", 
                             (multi_fabric_total_cost, stitching_id))
                
                conn.commit()
                
                # Log audit action
                log_audit_action(
                    user=self.current_user,
                    action_type="UPDATE",
                    entity="StitchingRecord",
                    entity_id=stitching_record['stitching_invoice_number'],
                    description=f"Updated stitching record {stitching_record['stitching_invoice_number']}",
                    details={
                        "stitched_item": stitched_item,
                        "size_qty": size_qty,
                        "price": price,
                        "total": total,
                        "lining_count": lining_table.rowCount(),
                        "lining_total": lining_total_cost,
                        "multi_fabric_count": multi_fabric_table.rowCount(),
                        "multi_fabric_total": multi_fabric_total_cost
                    }
                )
                
                QMessageBox.information(dialog, "Success", "Stitching record updated successfully.")
                
            except Exception as e:
                logger.error(f"DB error updating stitching record: {e}")
                QMessageBox.critical(dialog, "DB Error", f"Could not update stitching record: {e}")
            finally:
                cursor.close()
                conn.close()
            
            dialog.accept()
            self.refresh_stitching_lines_table()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(submit)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec()

    def refresh_stitching_lines_table(self):
        # Clear tree
        self.stitching_tree.clear()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get packing list mapping for stitching records
        cursor.execute("""
            SELECT pll.stitching_invoice_id, pl.packing_list_serial 
            FROM packing_list_lines pll 
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
        """)
        packing_list_map = {row['stitching_invoice_id']: row['packing_list_serial'] for row in cursor.fetchall()}
        
        # Get multi-fabric and lining data for all stitching records
        cursor.execute("""
            SELECT stitching_invoice_id, COUNT(*) as fabric_count
            FROM garment_fabrics 
            GROUP BY stitching_invoice_id
        """)
        multi_fabric_counts = {row['stitching_invoice_id']: row['fabric_count'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT stitching_invoice_id, COUNT(*) as lining_count
            FROM lining_fabrics 
            GROUP BY stitching_invoice_id
        """)
        lining_counts = {row['stitching_invoice_id']: row['lining_count'] for row in cursor.fetchall()}
        
        query = '''
            SELECT
              s.id, s.billing_group_id, s.stitching_invoice_number,
              s.stitched_item, s.item_name,
              l.color,
              c.short_name AS customer,
              i.tax_invoice_number,
              i.invoice_number AS fabric_invoice_number,
              l.delivery_note,
              s.yard_consumed,
              s.size_qty_json, s.price, s.total_value, s.add_vat, s.created_at,
              l.unit_price AS fabric_unit_price
            FROM stitching_invoices s
            LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
            LEFT JOIN invoices i ON l.invoice_id = i.id
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE 1=1
        '''
        params = []
        if self.filter_pl_number.currentText():
            query += " AND s.id IN (SELECT pll.stitching_invoice_id FROM packing_list_lines pll JOIN packing_lists pl ON pll.packing_list_id = pl.id WHERE pl.packing_list_serial LIKE %s)"
            params.append(f"%{self.filter_pl_number.currentText()}%")
        if self.filter_fabric_name.currentText():
            query += " AND s.item_name LIKE %s"
            params.append(f"%{self.filter_fabric_name.currentText()}%")
        if self.filter_customer_stitch.currentText():
            query += " AND (SELECT c.short_name FROM customers c JOIN invoices i ON c.id = i.customer_id JOIN invoice_lines l ON l.invoice_id = i.id WHERE l.item_name = s.item_name LIMIT 1) LIKE %s"
            params.append(f"%{self.filter_customer_stitch.currentText()}%")
        if self.filter_serial_number.currentText():
            query += " AND s.stitching_invoice_number LIKE %s"
            params.append(f"%{self.filter_serial_number.currentText()}%")
        # Apply in-stock/delivered/all filter
        if self.show_grouped.isChecked():
            query += " AND s.id IN (SELECT DISTINCT stitching_invoice_id FROM packing_list_lines)"
        elif self.show_non_grouped.isChecked():
            query += " AND s.id NOT IN (SELECT DISTINCT stitching_invoice_id FROM packing_list_lines)"
        # else if All is checked, do not filter by grouped/non-grouped
        query += " ORDER BY s.created_at DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        for row in rows:
            try:
                size_qty = eval(row['size_qty_json']) if row['size_qty_json'] else {}
            except Exception:
                size_qty = {}
            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            delivery_date = format_ddmmyy(row.get('invoice_date'))
            # Get packing list number instead of group number
            packing_list_number = packing_list_map.get(row['id'], '')
            
            # Calculate fabric value and total fabric amount
            fabric_unit_price = row.get('fabric_unit_price', 0) or 0
            yards_consumed = row.get('yard_consumed', 0) or 0
            fabric_cost = fabric_unit_price
            fabric_value = fabric_unit_price * yards_consumed
            
            # Calculate VAT-inclusive price for display
            base_price = float(row['price'] or 0)
            add_vat = row.get('add_vat', False)
            if add_vat:
                vat_amount = base_price * 0.07
                vat_inclusive_price = base_price + vat_amount
            else:
                vat_inclusive_price = base_price
            
            invoice_values = [
                packing_list_number,
                row.get('stitching_invoice_number', ''),
                row['stitched_item'],
                row['item_name'],
                row.get('color', ''),
                row.get('customer', ''),
                row.get('tax_invoice_number', '') or '',  # Tax Inv #
                row.get('fabric_invoice_number', ''),
                row.get('delivery_note', ''),
                format_number(row.get('yard_consumed', 0)),  # Fab Used
                format_number(fabric_cost),  # Fab Cost
                format_number(fabric_value),  # Fab Value
                format_integer(size_qty.get("S", 0)),
                format_integer(size_qty.get("M", 0)),
                format_integer(size_qty.get("L", 0)),
                format_integer(size_qty.get("XL", 0)),
                format_integer(size_qty.get("XXL", 0)),
                format_integer(size_qty.get("XXXL", 0)),
                format_integer(total_qty),
                format_number(vat_inclusive_price),  # Sew Cost (VAT inclusive)
                format_number(row['total_value']),  # Sew Value
                # Calculate Yd/Pcs (yards per piece)
                format_number(row.get('yard_consumed', 0) / total_qty if total_qty > 0 else 0, decimals=3),  # Yd/Pcs
                # Calculate Grmt Cost (garment cost per piece)
                format_number(self.calculate_garment_cost_per_piece(row, total_qty)),  # Grmt Cost
                row['created_at'].strftime('%d/%m/%y %H:%M') if row['created_at'] else ''
            ]
            # Create parent tree item
            parent_item = QTreeWidgetItem(self.stitching_tree)
            
            # Check if this stitching record has multiple fabrics or lining
            has_multi_fabric = multi_fabric_counts.get(row['id'], 0) > 0
            has_lining = lining_counts.get(row['id'], 0) > 0
            is_expandable = has_multi_fabric or has_lining
            
            # Set parent item data
            for col_idx, val in enumerate(invoice_values):
                parent_item.setText(col_idx, str(val))
                
                # Store stitching ID in the first column item for edit functionality
                if col_idx == 0:
                    parent_item.setData(col_idx, Qt.ItemDataRole.UserRole, row['id'])
                    # Add expand/collapse indicator for multi-fabric records
                    if is_expandable:
                        parent_item.setText(col_idx, "▶ " + str(val))
                        parent_item.setData(col_idx, Qt.ItemDataRole.UserRole + 1, True)  # Mark as expandable
            
            # Add child items for multi-fabrics if expandable
            if is_expandable:
                # Add multi-fabric details
                if has_multi_fabric:
                    cursor.execute("""
                        SELECT gf.*, l.item_name, l.color, i.invoice_number
                        FROM garment_fabrics gf
                        JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
                        JOIN invoices i ON l.invoice_id = i.id
                        WHERE gf.stitching_invoice_id = %s
                        ORDER BY l.item_name, l.color
                    """, (row['id'],))
                    multi_fabrics = cursor.fetchall()
                    
                    for fabric in multi_fabrics:
                        child_item = QTreeWidgetItem(parent_item)
                        
                        # Create child item with fabric details - align with parent columns
                        child_values = [
                            "",  # Packing List (empty for child)
                            "  └─ " + fabric['item_name'],  # Serial # (indented fabric name)
                            "",  # Stitched Item
                            fabric['item_name'],  # Fabric Name
                            fabric['color'],  # Color
                            "",  # Customer
                            "",  # Tax Inv #
                            fabric['invoice_number'],  # Fabric Inv #
                            "",  # Delivery Note
                            format_number(fabric['consumption_yards']),  # Fab Used
                            format_number(fabric['unit_price']),  # Fab Cost
                            format_number(fabric['total_fabric_cost']),  # Fab Value
                            "", "", "", "", "", "",  # Size columns (S, M, L, XL, XXL, XXXL, Total)
                            "",  # Sew Cost
                            "",  # Sew Value
                            "",  # Yd/Pcs
                            "",  # Grmt Cost
                            ""   # Created At
                        ]
                        
                        # Set text directly for each column (like packing list)
                        child_item.setText(0, "")  # PL# (empty for child)
                        child_item.setText(1, "")  # Serial # (empty for child)
                        child_item.setText(2, "")  # Stitched Item
                        child_item.setText(3, fabric['item_name'])  # Fabric Name
                        child_item.setText(4, fabric['color'])  # Color
                        child_item.setText(5, "")  # Customer
                        child_item.setText(6, "")  # Tax Inv #
                        child_item.setText(7, fabric['invoice_number'])  # Fabric Inv #
                        child_item.setText(8, "")  # Delivery Note
                        child_item.setText(9, format_number(fabric['consumption_yards']))  # Fab Used
                        child_item.setText(10, format_number(fabric['unit_price']))  # Fab Cost
                        child_item.setText(11, format_number(fabric['total_fabric_cost']))  # Fab Value
                        child_item.setText(12, "")  # S
                        child_item.setText(13, "")  # M
                        child_item.setText(14, "")  # L
                        child_item.setText(15, "")  # XL
                        child_item.setText(16, "")  # XXL
                        # Calculate yards per piece for child fabric
                        try:
                            size_qty = eval(row['size_qty_json']) if row['size_qty_json'] else {}
                            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                            yards_per_piece = float(fabric['consumption_yards']) / total_qty if total_qty > 0 else 0
                        except:
                            yards_per_piece = 0
                        
                        child_item.setText(17, "")  # XXXL
                        child_item.setText(18, "")  # Total Qty
                        child_item.setText(19, "")  # Sew Cost
                        child_item.setText(20, "")  # Sew Value
                        child_item.setText(21, format_number(yards_per_piece, decimals=3))  # Yd/Pcs
                        child_item.setText(22, "")  # Grmt Cost
                        child_item.setText(23, "")  # Created At
                        
                        # Set data for functionality
                        child_item.setData(0, Qt.ItemDataRole.UserRole, row['id'])  # Parent ID
                        child_item.setData(0, Qt.ItemDataRole.UserRole + 2, "multi_fabric")  # Type
                
                # Add lining fabric details
                if has_lining:
                    cursor.execute("""
                        SELECT * FROM lining_fabrics 
                        WHERE stitching_invoice_id = %s
                        ORDER BY lining_name
                    """, (row['id'],))
                    lining_fabrics = cursor.fetchall()
                    
                    for lining in lining_fabrics:
                        child_item = QTreeWidgetItem(parent_item)
                        
                        # Create child item with lining details - align with parent columns
                        child_values = [
                            "",  # Packing List (empty for child)
                            "  └─ " + lining['lining_name'],  # Serial # (indented lining name)
                            "",  # Stitched Item
                            lining['lining_name'],  # Fabric Name (lining name)
                            "",  # Color (empty for lining)
                            "",  # Customer
                            "",  # Tax Inv #
                            "",  # Fabric Inv #
                            "",  # Delivery Note
                            format_number(lining['consumption_yards']),  # Fab Used
                            format_number(lining['unit_price']),  # Fab Cost
                            format_number(lining['total_cost']),  # Fab Value
                            "", "", "", "", "", "",  # Size columns (S, M, L, XL, XXL, XXXL, Total)
                            "",  # Sew Cost
                            "",  # Sew Value
                            "",  # Yd/Pcs
                            "",  # Grmt Cost
                            ""   # Created At
                        ]
                        
                        # Set text directly for each column (like packing list)
                        child_item.setText(0, "")  # PL# (empty for child)
                        child_item.setText(1, "")  # Serial # (empty for child)
                        child_item.setText(2, "")  # Stitched Item
                        child_item.setText(3, lining['lining_name'])  # Fabric Name (lining name)
                        child_item.setText(4, "")  # Color (empty for lining)
                        child_item.setText(5, "")  # Customer
                        child_item.setText(6, "")  # Tax Inv #
                        child_item.setText(7, "")  # Fabric Inv #
                        child_item.setText(8, "")  # Delivery Note
                        child_item.setText(9, format_number(lining['consumption_yards']))  # Fab Used
                        child_item.setText(10, format_number(lining['unit_price']))  # Fab Cost
                        child_item.setText(11, format_number(lining['total_cost']))  # Fab Value
                        child_item.setText(12, "")  # S
                        child_item.setText(13, "")  # M
                        child_item.setText(14, "")  # L
                        child_item.setText(15, "")  # XL
                        child_item.setText(16, "")  # XXL
                        # Calculate yards per piece for child lining
                        try:
                            size_qty = eval(row['size_qty_json']) if row['size_qty_json'] else {}
                            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                            yards_per_piece = float(lining['consumption_yards']) / total_qty if total_qty > 0 else 0
                        except:
                            yards_per_piece = 0
                        
                        child_item.setText(17, "")  # XXXL
                        child_item.setText(18, "")  # Total Qty
                        child_item.setText(19, "")  # Sew Cost
                        child_item.setText(20, "")  # Sew Value
                        child_item.setText(21, format_number(yards_per_piece, decimals=3))  # Yd/Pcs
                        child_item.setText(22, "")  # Grmt Cost
                        child_item.setText(23, "")  # Created At
                        
                        # Set data for functionality
                        child_item.setData(0, Qt.ItemDataRole.UserRole, row['id'])  # Parent ID
                        child_item.setData(0, Qt.ItemDataRole.UserRole + 2, "lining")  # Type
        cursor.close()
        conn.close()
        # Populate filter comboboxes with unique values
        self.populate_stitching_filters()
        
        # Connect double-click to expand/collapse functionality
        self.stitching_tree.itemDoubleClicked.connect(self.on_stitching_item_double_clicked)

    def populate_stitching_filters(self):
        def get_unique_stitching_values():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT item_name FROM stitching_invoices ORDER BY item_name")
            items = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT stitched_item FROM stitching_invoices ORDER BY stitched_item")
            stitched_items = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("""
                SELECT DISTINCT c.short_name 
                FROM stitching_invoices s 
                LEFT JOIN invoice_lines l ON s.item_name = l.item_name 
                LEFT JOIN invoices i ON l.invoice_id = i.id 
                LEFT JOIN customers c ON i.customer_id = c.id 
                WHERE c.short_name IS NOT NULL 
                ORDER BY c.short_name
            """)
            customers = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("SELECT DISTINCT stitching_invoice_number FROM stitching_invoices ORDER BY stitching_invoice_number")
            serials = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.execute("""
                SELECT DISTINCT pl.packing_list_serial 
                FROM stitching_invoices s 
                LEFT JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id 
                LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id 
                WHERE pl.packing_list_serial IS NOT NULL 
                ORDER BY pl.packing_list_serial
            """)
            pl_numbers = [r[0] for r in cursor.fetchall() if r[0]]
            cursor.close()
            conn.close()
            return items, stitched_items, customers, serials, pl_numbers
        items, stitched_items, customers, serials, pl_numbers = get_unique_stitching_values()
        # Only repopulate if not currently filtering
        if not self.filter_fabric_name.currentText():
            self.filter_fabric_name.clear()
            self.filter_fabric_name.addItem("")
            self.filter_fabric_name.addItems(items)
        if not self.filter_customer_stitch.currentText():
            self.filter_customer_stitch.clear()
            self.filter_customer_stitch.addItem("")
            self.filter_customer_stitch.addItems(customers)
        if not self.filter_serial_number.currentText():
            self.filter_serial_number.clear()
            self.filter_serial_number.addItem("")
            self.filter_serial_number.addItems(serials)
        if not self.filter_pl_number.currentText():
            self.filter_pl_number.clear()
            self.filter_pl_number.addItem("")
            self.filter_pl_number.addItems(pl_numbers)
        # Connect filter changes to debounced update
        self.filter_pl_number.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_fabric_name.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_customer_stitch.currentTextChanged.connect(self.trigger_filter_update)
        self.filter_serial_number.currentTextChanged.connect(self.trigger_filter_update)
        # Stitching Record radio toggle (already immediate, but ensure no debouncing is used)
        self.show_grouped_var.buttonClicked.connect(self.refresh_stitching_lines_table)

    def refresh_packing_list_table(self):
        # Clear tree
        self.packing_tree.clear()
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = '''SELECT pl.*, c.short_name as customer_name FROM packing_lists pl LEFT JOIN customers c ON pl.customer_id = c.id WHERE 1=1'''
            params = []
            # Apply filters
            if self.pl_filter_serial.currentText():
                query += " AND pl.packing_list_serial LIKE %s"
                params.append(f"%{self.pl_filter_serial.currentText()}%")
            if self.pl_filter_stitch_serial.currentText():
                query += " AND pl.id IN (SELECT pll.packing_list_id FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id WHERE s.stitching_invoice_number LIKE %s)"
                params.append(f"%{self.pl_filter_stitch_serial.currentText()}%")
            if self.pl_filter_fabric.currentText():
                query += " AND pl.id IN (SELECT pll.packing_list_id FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id WHERE l.item_name LIKE %s)"
                params.append(f"%{self.pl_filter_fabric.currentText()}%")
            if self.pl_filter_customer.currentText():
                query += " AND c.short_name LIKE %s"
                params.append(f"%{self.pl_filter_customer.currentText()}%")
            if self.pl_filter_taxinv.currentText():
                query += " AND pl.id IN (SELECT pll.packing_list_id FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id WHERE i.tax_invoice_number LIKE %s)"
                params.append(f"%{self.pl_filter_taxinv.currentText()}%")
            if self.pl_filter_fabinv.currentText():
                query += " AND pl.id IN (SELECT pll.packing_list_id FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id WHERE i.invoice_number LIKE %s)"
                params.append(f"%{self.pl_filter_fabinv.currentText()}%")
            if self.pl_filter_fabdn.currentText():
                query += " AND pl.id IN (SELECT pll.packing_list_id FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id WHERE l.delivery_note LIKE %s)"
                params.append(f"%{self.pl_filter_fabdn.currentText()}%")
            date_from = self.pl_filter_date_from.text().strip()
            date_to = self.pl_filter_date_to.text().strip()
            if date_from:
                try:
                    if len(date_from) == 8 and date_from.count('/') == 2:
                        day, month, year = date_from.split('/')
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        date_from_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        query += " AND DATE(pl.created_at) >= %s"
                        params.append(date_from_iso)
                except (ValueError, IndexError):
                    pass
            if date_to:
                try:
                    if len(date_to) == 8 and date_to.count('/') == 2:
                        day, month, year = date_to.split('/')
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        date_to_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        query += " AND DATE(pl.created_at) <= %s"
                        params.append(date_to_iso)
                except (ValueError, IndexError):
                    pass
            # Efficient billed/unbilled/all filter
            if self.pl_show_billed.isChecked():
                query += " AND EXISTS (SELECT 1 FROM stitching_invoice_group_lines sigl JOIN stitching_invoices s ON sigl.stitching_invoice_id = s.id JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id WHERE pll.packing_list_id = pl.id)"
            elif self.pl_show_unbilled.isChecked():
                query += " AND NOT EXISTS (SELECT 1 FROM stitching_invoice_group_lines sigl JOIN stitching_invoices s ON sigl.stitching_invoice_id = s.id JOIN packing_list_lines pll ON s.id = pll.stitching_invoice_id WHERE pll.packing_list_id = pl.id)"
            # else if All is checked, do not filter by group billing
            query += " ORDER BY pl.created_at DESC"
            cursor.execute(query, params)
            packing_lists = cursor.fetchall()
            
            for pl in packing_lists:
                # Create parent item (packing list summary)
                parent_item = QTreeWidgetItem(self.packing_tree)
                parent_item.setText(0, pl.get('packing_list_serial', 'N/A'))  # PL #
                parent_item.setText(1, f"Summary ({pl.get('total_records', 0)} records)")  # Serial # (summary)
                parent_item.setText(2, f"Total Items: {pl.get('total_items', 0)}")  # Garment (summary)
                parent_item.setText(3, "")  # Fabric
                parent_item.setText(4, "")  # Color
                parent_item.setText(5, pl.get('customer_name', '') or '')  # Customer
                parent_item.setText(6, pl.get('tax_invoice_number', '') or '')  # Tax Inv # (parent only)
                parent_item.setText(7, "")  # Fabric Inv.
                parent_item.setText(8, "")  # Fabric DN.
                parent_item.setText(9, "")  # Fab Used
                parent_item.setText(10, "")  # Fab Cost
                parent_item.setText(11, "")  # Fab Value
                parent_item.setText(12, "")  # S
                parent_item.setText(13, "")  # M
                parent_item.setText(14, "")  # L
                parent_item.setText(15, "")  # XL
                parent_item.setText(16, "")  # XXL
                parent_item.setText(17, "")  # XXXL
                parent_item.setText(18, format_integer(pl.get('total_items', 0)))  # Total Qty
                parent_item.setText(19, "")  # Sew Cost
                parent_item.setText(20, "")  # Sew Value
                # Use delivery_date if available, otherwise fall back to created_at
                display_date = pl.get('delivery_date') or pl.get('created_at')
                parent_item.setText(21, format_ddmmyy(display_date) if display_date else '')  # Created At
                parent_item.setData(0, Qt.ItemDataRole.UserRole, pl.get('id'))
                # Get stitching records for this packing list
                try:
                    cursor.execute('''
                        SELECT s.*, l.color, i.invoice_number, i.tax_invoice_number, i.invoice_date, l.item_name as fabric_name, l.unit_price as fabric_unit_price, l.delivery_note
                        FROM packing_list_lines pll
                        JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id
                        LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
                        LEFT JOIN invoices i ON l.invoice_id = i.id
                        WHERE pll.packing_list_id=%s
                    ''', (pl.get('id'),))
                    stitching_records = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch stitching records for packing list {pl.get('id')}: {e}")
                    stitching_records = []
                for record in stitching_records:
                    # Create child item (stitching record)
                    child_item = QTreeWidgetItem(parent_item)
                    
                    # Check if this stitching record has multiple fabrics or lining
                    has_multi_fabric = self.has_multi_fabric_or_lining(record.get('id'))
                    
                    # Calculate fabric values
                    fabric_unit_price = record.get('fabric_unit_price', 0) or 0
                    yards_consumed = record.get('yard_consumed', 0) or 0
                    fabric_cost = fabric_unit_price
                    fabric_value = fabric_unit_price * yards_consumed
                    
                    # Add expand indicator if has multi-fabric
                    serial_text = record.get('stitching_invoice_number', '')
                    if has_multi_fabric:
                        serial_text = "▶ " + serial_text
                    
                    child_item.setText(0, pl.get('packing_list_serial', 'N/A'))  # PL #
                    child_item.setText(1, serial_text)  # Serial #
                    child_item.setText(2, record.get('stitched_item', ''))  # Garment
                    child_item.setText(3, record.get('fabric_name', '') or '')  # Fabric
                    child_item.setText(4, record.get('color', '') or '')  # Color
                    child_item.setText(5, pl.get('customer_name', '') or '')  # Customer
                    child_item.setText(6, record.get('tax_invoice_number', '') or '')  # Tax Inv # (child row: fabric tax invoice number)
                    child_item.setText(7, record.get('invoice_number', '') or '')  # Fabric Inv.
                    child_item.setText(8, record.get('delivery_note', '') or '')  # Fabric DN.
                    child_item.setText(9, format_number(yards_consumed))  # Fab Used
                    child_item.setText(10, format_number(fabric_cost))  # Fab Cost
                    child_item.setText(11, format_number(fabric_value))  # Fab Value
                    try:
                        size_qty = eval(record.get('size_qty_json', '{}')) if record.get('size_qty_json') else {}
                    except Exception:
                        size_qty = {}
                    child_item.setText(12, format_integer(size_qty.get("S", 0)))
                    child_item.setText(13, format_integer(size_qty.get("M", 0)))  # M
                    child_item.setText(14, format_integer(size_qty.get("L", 0)))  # L
                    child_item.setText(15, format_integer(size_qty.get("XL", 0)))  # XL
                    child_item.setText(16, format_integer(size_qty.get("XXL", 0)))  # XXL
                    child_item.setText(17, format_integer(size_qty.get("XXXL", 0)))  # XXXL
                    total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                    child_item.setText(18, format_integer(total_qty))  # Total Qty
                    # Calculate VAT-inclusive price for display
                    base_price = float(record.get('price', 0) or 0)
                    add_vat = record.get('add_vat', False)
                    if add_vat:
                        vat_amount = base_price * 0.07
                        vat_inclusive_price = base_price + vat_amount
                    else:
                        vat_inclusive_price = base_price
                    child_item.setText(19, format_number(vat_inclusive_price))  # Sew Cost (VAT inclusive)
                    child_item.setText(20, format_number(record.get('total_value', '')))  # Sew Value
                    child_item.setText(21, format_ddmmyy(record.get('created_at')))  # Created At
                    child_item.setData(0, Qt.ItemDataRole.UserRole, record.get('id'))  # Store stitching_invoice_id
                    
                    # Add multi-fabric details as sub-items if they exist
                    if has_multi_fabric:
                        # Get multi-fabric details
                        cursor.execute("""
                            SELECT gf.*, l.item_name, l.color, i.invoice_number
                            FROM garment_fabrics gf
                            JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
                            JOIN invoices i ON l.invoice_id = i.id
                            WHERE gf.stitching_invoice_id = %s
                            ORDER BY l.item_name, l.color
                        """, (record.get('id'),))
                        multi_fabrics = cursor.fetchall()
                        
                        # Get lining fabric details
                        cursor.execute("""
                            SELECT * FROM lining_fabrics 
                            WHERE stitching_invoice_id = %s
                            ORDER BY lining_name
                        """, (record.get('id'),))
                        lining_fabrics = cursor.fetchall()
                        
                        # Add multi-fabric sub-items
                        for fabric in multi_fabrics:
                            sub_item = QTreeWidgetItem(child_item)
                            sub_item.setText(0, pl.get('packing_list_serial', 'N/A'))  # PL #
                            sub_item.setText(1, "  └─ " + fabric['item_name'])  # Serial # (indented fabric name)
                            sub_item.setText(2, "")  # Garment
                            sub_item.setText(3, fabric['item_name'])  # Fabric
                            sub_item.setText(4, fabric['color'])  # Color
                            sub_item.setText(5, pl.get('customer_name', '') or '')  # Customer
                            sub_item.setText(6, "")  # Tax Inv #
                            sub_item.setText(7, fabric['invoice_number'])  # Fabric Inv.
                            sub_item.setText(8, "")  # Fabric DN.
                            sub_item.setText(9, format_number(fabric['consumption_yards']))  # Fab Used
                            sub_item.setText(10, format_number(fabric['unit_price']))  # Fab Cost
                            sub_item.setText(11, format_number(fabric['total_fabric_cost']))  # Fab Value
                            sub_item.setText(12, "")  # S
                            sub_item.setText(13, "")  # M
                            sub_item.setText(14, "")  # L
                            sub_item.setText(15, "")  # XL
                            sub_item.setText(16, "")  # XXL
                            sub_item.setText(17, "")  # XXXL
                            sub_item.setText(18, "")  # Total Qty
                            sub_item.setText(19, "")  # Sew Cost
                            sub_item.setText(20, "")  # Sew Value
                            sub_item.setText(21, "")  # Created At
                            sub_item.setData(0, Qt.ItemDataRole.UserRole, record.get('id'))  # Store parent stitching_invoice_id
                            sub_item.setData(1, Qt.ItemDataRole.UserRole, "multi_fabric")  # Type
                        
                        # Add lining fabric sub-items
                        for lining in lining_fabrics:
                            sub_item = QTreeWidgetItem(child_item)
                            sub_item.setText(0, pl.get('packing_list_serial', 'N/A'))  # PL #
                            sub_item.setText(1, "  └─ " + lining['lining_name'])  # Serial # (indented lining name)
                            sub_item.setText(2, "")  # Garment
                            sub_item.setText(3, lining['lining_name'])  # Fabric
                            sub_item.setText(4, "")  # Color
                            sub_item.setText(5, pl.get('customer_name', '') or '')  # Customer
                            sub_item.setText(6, "")  # Tax Inv #
                            sub_item.setText(7, "")  # Fabric Inv.
                            sub_item.setText(8, "")  # Fabric DN.
                            sub_item.setText(9, format_number(lining['consumption_yards']))  # Fab Used
                            sub_item.setText(10, format_number(lining['unit_price']))  # Fab Cost
                            sub_item.setText(11, format_number(lining['total_cost']))  # Fab Value
                            sub_item.setText(12, "")  # S
                            sub_item.setText(13, "")  # M
                            sub_item.setText(14, "")  # L
                            sub_item.setText(15, "")  # XL
                            sub_item.setText(16, "")  # XXL
                            sub_item.setText(17, "")  # XXXL
                            sub_item.setText(18, "")  # Total Qty
                            sub_item.setText(19, "")  # Sew Cost
                            sub_item.setText(20, "")  # Sew Value
                            sub_item.setText(21, "")  # Created At
                            sub_item.setData(0, Qt.ItemDataRole.UserRole, record.get('id'))  # Store parent stitching_invoice_id
                            sub_item.setData(1, Qt.ItemDataRole.UserRole, "lining")  # Type
            
            cursor.close()
            conn.close()
            
            # Populate filter comboboxes
            self.populate_packing_list_filters()
            
            # Connect double-click to expand/collapse functionality
            self.packing_tree.itemDoubleClicked.connect(self.on_packing_item_double_clicked)
            
        except Exception as e:
            logger.error(f"Error refreshing packing list table: {e}")
            # Don't show error message to user, just log it
            # The table will be empty, which is fine for a new installation

    def populate_packing_list_filters(self):
        def get_unique_packing_list_values():
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT packing_list_serial FROM packing_lists GROUP BY packing_list_serial ORDER BY packing_list_serial")
            serials = [row[0] for row in cursor.fetchall()]
            # Serial # (from stitching_invoices in packing_list_lines)
            cursor.execute("SELECT DISTINCT s.stitching_invoice_number FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id ORDER BY s.stitching_invoice_number")
            stitch_serials = [row[0] for row in cursor.fetchall() if row[0]]
            # Fabric
            cursor.execute("SELECT DISTINCT l.item_name FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id ORDER BY l.item_name")
            fabrics = [row[0] for row in cursor.fetchall() if row[0]]
            # Customer
            cursor.execute("SELECT c.short_name FROM packing_lists pl JOIN customers c ON pl.customer_id = c.id GROUP BY c.short_name ORDER BY c.short_name")
            customers = [row[0] for row in cursor.fetchall() if row[0]]
            # Tax Inv #
            cursor.execute("SELECT DISTINCT i.tax_invoice_number FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id ORDER BY i.tax_invoice_number")
            taxinvs = [row[0] for row in cursor.fetchall() if row[0]]
            # Fabric Inv
            cursor.execute("SELECT DISTINCT i.invoice_number FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id LEFT JOIN invoices i ON l.invoice_id = i.id ORDER BY i.invoice_number")
            fabinvs = [row[0] for row in cursor.fetchall() if row[0]]
            # Fabric DN
            cursor.execute("SELECT DISTINCT l.delivery_note FROM packing_list_lines pll JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id ORDER BY l.delivery_note")
            fabdns = [row[0] for row in cursor.fetchall() if row[0]]
            cursor.close()
            conn.close()
            return serials, stitch_serials, fabrics, customers, taxinvs, fabinvs, fabdns
        serials, stitch_serials, fabrics, customers, taxinvs, fabinvs, fabdns = get_unique_packing_list_values()
        # Only repopulate if not currently filtering
        if not self.pl_filter_serial.currentText():
            self.pl_filter_serial.clear()
            self.pl_filter_serial.addItem("")
            self.pl_filter_serial.addItems(serials)
        if not self.pl_filter_stitch_serial.currentText():
            self.pl_filter_stitch_serial.clear()
            self.pl_filter_stitch_serial.addItem("")
            self.pl_filter_stitch_serial.addItems(stitch_serials)
        if not self.pl_filter_fabric.currentText():
            self.pl_filter_fabric.clear()
            self.pl_filter_fabric.addItem("")
            self.pl_filter_fabric.addItems(fabrics)
        if not self.pl_filter_customer.currentText():
            self.pl_filter_customer.clear()
            self.pl_filter_customer.addItem("")
            self.pl_filter_customer.addItems(customers)
        if not self.pl_filter_taxinv.currentText():
            self.pl_filter_taxinv.clear()
            self.pl_filter_taxinv.addItem("")
            self.pl_filter_taxinv.addItems(taxinvs)
        if not self.pl_filter_fabinv.currentText():
            self.pl_filter_fabinv.clear()
            self.pl_filter_fabinv.addItem("")
            self.pl_filter_fabinv.addItems(fabinvs)
        if not self.pl_filter_fabdn.currentText():
            self.pl_filter_fabdn.clear()
            self.pl_filter_fabdn.addItem("")
            self.pl_filter_fabdn.addItems(fabdns)
        # Connect filter changes to debounced update
        self.pl_filter_serial.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_stitch_serial.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_fabric.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_customer.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_taxinv.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_fabinv.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_fabdn.currentTextChanged.connect(self.trigger_filter_update)
        self.pl_filter_date_from.textChanged.connect(self.trigger_filter_update)
        self.pl_filter_date_to.textChanged.connect(self.trigger_filter_update)

    def on_packing_item_double_clicked(self, item, column):
        """Handle double-click on packing list tree items"""
        # Check if this is a stitching record with expand indicator
        if column == 1:  # Serial # column
            text = item.text(1)
            if text.startswith("▶ "):
                # This is an expandable stitching record
                self.toggle_packing_item_expansion(item)
                return
        
        # Handle regular double-click for PDF viewing
        self.view_packing_list_pdf_from_tree()
    
    def toggle_packing_item_expansion(self, item):
        """Toggle expansion of a packing list item"""
        text = item.text(1)
        stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if currently expanded (has ▼) or collapsed (has ▶)
        is_expanded = "▼" in text
        
        if is_expanded:
            # Collapse: hide child items and change to ▶
            self.collapse_packing_item(item)
            item.setText(1, "▶ " + text.replace("▼ ", ""))
        else:
            # Expand: show child items and change to ▼
            self.expand_packing_item(item, stitching_id)
            item.setText(1, "▼ " + text.replace("▶ ", ""))
    
    def expand_packing_item(self, item, stitching_id):
        """Expand a packing list item to show child fabrics"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get multi-fabric details
        cursor.execute("""
            SELECT gf.*, l.item_name, l.color, i.invoice_number
            FROM garment_fabrics gf
            JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
            JOIN invoices i ON l.invoice_id = i.id
            WHERE gf.stitching_invoice_id = %s
            ORDER BY l.item_name, l.color
        """, (stitching_id,))
        multi_fabrics = cursor.fetchall()
        
        # Get lining fabric details
        cursor.execute("""
            SELECT * FROM lining_fabrics 
            WHERE stitching_invoice_id = %s
            ORDER BY lining_name
        """, (stitching_id,))
        lining_fabrics = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Get packing list info for sub-items
        packing_list_serial = item.text(0)
        customer_name = item.text(5)
        
        # Add multi-fabric sub-items
        for fabric in multi_fabrics:
            sub_item = QTreeWidgetItem(item)
            sub_item.setText(0, packing_list_serial)  # PL #
            sub_item.setText(1, "  └─ " + fabric['item_name'])  # Serial # (indented fabric name)
            sub_item.setText(2, "")  # Garment
            sub_item.setText(3, fabric['item_name'])  # Fabric
            sub_item.setText(4, fabric['color'])  # Color
            sub_item.setText(5, customer_name)  # Customer
            sub_item.setText(6, "")  # Tax Inv #
            sub_item.setText(7, fabric['invoice_number'])  # Fabric Inv.
            sub_item.setText(8, "")  # Fabric DN.
            sub_item.setText(9, format_number(fabric['consumption_yards']))  # Fab Used
            sub_item.setText(10, format_number(fabric['unit_price']))  # Fab Cost
            sub_item.setText(11, format_number(fabric['total_fabric_cost']))  # Fab Value
            sub_item.setText(12, "")  # S
            sub_item.setText(13, "")  # M
            sub_item.setText(14, "")  # L
            sub_item.setText(15, "")  # XL
            sub_item.setText(16, "")  # XXL
            sub_item.setText(17, "")  # XXXL
            sub_item.setText(18, "")  # Total Qty
            sub_item.setText(19, "")  # Sew Cost
            sub_item.setText(20, "")  # Sew Value
            sub_item.setText(21, "")  # Created At
            sub_item.setData(0, Qt.ItemDataRole.UserRole, stitching_id)  # Store parent stitching_invoice_id
            sub_item.setData(1, Qt.ItemDataRole.UserRole, "multi_fabric")  # Type
        
        # Add lining fabric sub-items
        for lining in lining_fabrics:
            sub_item = QTreeWidgetItem(item)
            sub_item.setText(0, packing_list_serial)  # PL #
            sub_item.setText(1, "  └─ " + lining['lining_name'])  # Serial # (indented lining name)
            sub_item.setText(2, "")  # Garment
            sub_item.setText(3, lining['lining_name'])  # Fabric
            sub_item.setText(4, "")  # Color
            sub_item.setText(5, customer_name)  # Customer
            sub_item.setText(6, "")  # Tax Inv #
            sub_item.setText(7, "")  # Fabric Inv.
            sub_item.setText(8, "")  # Fabric DN.
            sub_item.setText(9, format_number(lining['consumption_yards']))  # Fab Used
            sub_item.setText(10, format_number(lining['unit_price']))  # Fab Cost
            sub_item.setText(11, format_number(lining['total_cost']))  # Fab Value
            sub_item.setText(12, "")  # S
            sub_item.setText(13, "")  # M
            sub_item.setText(14, "")  # L
            sub_item.setText(15, "")  # XL
            sub_item.setText(16, "")  # XXL
            sub_item.setText(17, "")  # XXXL
            sub_item.setText(18, "")  # Total Qty
            sub_item.setText(19, "")  # Sew Cost
            sub_item.setText(20, "")  # Sew Value
            sub_item.setText(21, "")  # Created At
            sub_item.setData(0, Qt.ItemDataRole.UserRole, stitching_id)  # Store parent stitching_invoice_id
            sub_item.setData(1, Qt.ItemDataRole.UserRole, "lining")  # Type
    
    def collapse_packing_item(self, item):
        """Collapse a packing list item to hide child fabrics"""
        # Remove all child items
        while item.childCount() > 0:
            item.removeChild(item.child(0))
    
    def view_packing_list_pdf_from_tree(self):
        selected_items = self.packing_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Select a packing list to view its PDF.")
            return
        
        item = selected_items[0]
        packing_list_id = None
        
        if item.parent() is None:
            # It's a packing list item
            packing_list_id = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            # It's a stitching record item, get the parent packing list
            packing_list_item = item.parent()
            packing_list_id = packing_list_item.data(0, Qt.ItemDataRole.UserRole)
        
        if not packing_list_id:
            QMessageBox.information(self, "No Selection", "Select a packing list to view its PDF.")
            return
        
        # Create dialog for PDF viewing options
        dialog = QDialog(self)
        dialog.setWindowTitle("View Packing List PDF")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # Garment cost toggle
        cost_checkbox = QCheckBox("Display garment cost in packing list")
        cost_checkbox.setToolTip("Shows the calculated cost per garment: (Fabric Used × Fabric Price + Total Garments × Sewing Price) ÷ Total Garments")
        layout.addWidget(cost_checkbox)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get values from dialog
        show_garment_cost = cost_checkbox.isChecked()
        
        # Generate PDF with the selected options
        self.generate_grouped_packing_list_pdf(packing_list_id, view_after=True, comments="", show_garment_cost=show_garment_cost)

    def create_group_billing_note(self):
        """Create group billing note from selected packing lists"""
        selected_items = self.packing_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more packing lists to create a group billing note.")
            return
        
        # Get packing list IDs from selected items (only parent items, not child stitching records)
        packing_list_ids = []
        for item in selected_items:
            if item.parent() is None:  # Only parent items (packing lists)
                packing_list_id = item.data(0, Qt.ItemDataRole.UserRole)
                if packing_list_id:
                    packing_list_ids.append(packing_list_id)
        
        if not packing_list_ids:
            QMessageBox.information(self, "No Selection", "Please select packing lists (not individual stitching records) to create a group billing note.")
            return
        
        # Create dialog for group billing comments
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Group Billing Note")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(350)
        layout = QVBoxLayout(dialog)
        
        # Invoice Date
        layout.addWidget(QLabel("Invoice Date:"))
        invoice_date_edit = QDateEdit()
        invoice_date_edit.setDate(QDate.currentDate())
        invoice_date_edit.setCalendarPopup(True)
        layout.addWidget(invoice_date_edit)
        
        # Stitching Invoice Comments
        layout.addWidget(QLabel("Stitching Invoice Comments (optional):"))
        stitching_comments_text = QTextEdit()
        stitching_comments_text.setMaximumHeight(80)
        stitching_comments_text.setPlaceholderText("Enter comments for the stitching invoice...")
        layout.addWidget(stitching_comments_text)
        
        # Fabric Invoice Comments
        layout.addWidget(QLabel("Fabric Invoice Comments (optional):"))
        fabric_comments_text = QTextEdit()
        fabric_comments_text.setMaximumHeight(80)
        fabric_comments_text.setPlaceholderText("Enter comments for the fabric invoice...")
        layout.addWidget(fabric_comments_text)
        
        # Withholding Tax Option
        withholding_tax_checkbox = QCheckBox("Apply Withholding Tax (3%)")
        withholding_tax_checkbox.setToolTip("Apply 3% withholding tax to the subtotal amount")
        withholding_tax_checkbox.setChecked(True)  # Set to checked by default
        layout.addWidget(withholding_tax_checkbox)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get values from dialog
        invoice_date = invoice_date_edit.date().toPyDate()
        stitching_comments = stitching_comments_text.toPlainText().strip()
        fabric_comments = fabric_comments_text.toPlainText().strip()
        apply_withholding_tax = withholding_tax_checkbox.isChecked()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Generate group billing note serial number
            group_number = self.generate_serial_number("GBN")
            
            # Get customer_id from the first packing list
            cursor.execute("SELECT customer_id FROM packing_lists WHERE id = %s", (packing_list_ids[0],))
            customer_result = cursor.fetchone()
            if not customer_result:
                QMessageBox.critical(self, "Error", "Could not determine customer for selected packing lists.")
                cursor.close()
                conn.close()
                return
            
            customer_id = customer_result['customer_id']
            
            # Create group
            cursor.execute("""
                INSERT INTO stitching_invoice_groups (group_number, customer_id, created_at, invoice_date, stitching_comments, fabric_comments) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (group_number, customer_id, datetime.now(), invoice_date, stitching_comments, fabric_comments))
            group_id = cursor.lastrowid
            
            # Get all stitching records from the selected packing lists
            cursor.execute("""
                SELECT DISTINCT pll.stitching_invoice_id
                FROM packing_list_lines pll
                WHERE pll.packing_list_id IN ({})
            """.format(','.join(['%s'] * len(packing_list_ids))), tuple(packing_list_ids))
            
            stitching_ids = [row['stitching_invoice_id'] for row in cursor.fetchall()]
            
            # Link stitching records to group
            for sid in stitching_ids:
                cursor.execute("INSERT INTO stitching_invoice_group_lines (group_id, stitching_invoice_id) VALUES (%s, %s)", 
                             (group_id, sid))
                # Update stitching invoice to mark it as grouped
                cursor.execute("UPDATE stitching_invoices SET billing_group_id = %s WHERE id = %s", (group_id, sid))
            
            conn.commit()
            # Log audit action for group bill creation
            log_audit_action(
                user=self.current_user,
                action_type="CREATE",
                entity="GroupBill",
                entity_id=group_id,
                description=f"Created group bill {group_number} from packing lists {packing_list_ids}.",
                details={"group_number": group_number, "packing_list_ids": packing_list_ids, "stitching_ids": stitching_ids, "stitching_comments": stitching_comments, "fabric_comments": fabric_comments, "apply_withholding_tax": apply_withholding_tax}
            )
            # Generate PDFs after group creation
            self.generate_stitching_fee_pdf(group_id, view_after=False, show_success_dialog=True, apply_withholding_tax=apply_withholding_tax)
            self.generate_fabric_used_pdf(group_id, view_after=False, show_success_dialog=True)
            # Show the PDF dialog for this group
            self.show_pdf_dialog(group_id)
            return  # Skip the old success message
            
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="GroupBill",
                entity_id=None,
                description=f"Error creating group billing note: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            logger.error(f"Error creating group billing note: {e}")
            QMessageBox.critical(self, "Error", f"Could not create group billing note: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        
        # Refresh tables
        self.refresh_packing_list_table()
        self.refresh_group_bill_table()

    def create_grouped_packing_list(self):
        # Get selected items from stitching tree
        selected_items = self.stitching_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more stitching records to create a packing list.")
            return
        
        # Get the stitching record IDs
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True,buffered=True)
        stitching_ids = []
        customer_id = None
        
        for item in selected_items:
            # Only process parent items (stitching records), not child fabrics
            if item.parent() is None:
                stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
                if stitching_id:
                    serial = item.text(1)  # Serial # is col 1
            
            #check stitch invoice already created packing list
            cursor.execute("SELECT p.id FROM stitching_invoices as s inner join packing_list_lines as p " \
                "on s.id=p.stitching_invoice_id WHERE s.stitching_invoice_number=%s", (serial,))
            rowdata = cursor.fetchone()
            if rowdata:
                QMessageBox.critical(self, "Error", "Some selected stiching already generated packing list!")
                cursor.close()
                conn.close()
                return
            
            cursor.execute("SELECT id, billing_group_id FROM stitching_invoices WHERE stitching_invoice_number=%s", (serial,))
            rowdata = cursor.fetchone()
            if rowdata:
                stitching_ids.append(rowdata['id'])
                # Get customer_id from the first record
                if customer_id is None: #fixed 290725 : s.item_name = l.item_name
                    cursor.execute("""
                        SELECT i.customer_id FROM stitching_invoices s 
                        LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id  
                        LEFT JOIN invoices i ON l.invoice_id = i.id 
                        WHERE s.id=%s LIMIT 1
                    """, (rowdata['id'],))
                    customer_row = cursor.fetchone()
                    if customer_row:
                        customer_id = customer_row['customer_id']
        
        if not stitching_ids:
            QMessageBox.critical(self, "Error", "Could not find selected stitching records.")
            cursor.close()
            conn.close()
            return
        
        if not customer_id:
            QMessageBox.critical(self, "Error", "Could not determine customer for selected records.")
            cursor.close()
            conn.close()
            return
        
        # Create dialog for packing list options
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Packing List")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # Delivery Date
        layout.addWidget(QLabel("Delivery Date:"))
        delivery_date_edit = QDateEdit()
        delivery_date_edit.setDate(QDate.currentDate())
        delivery_date_edit.setCalendarPopup(True)
        layout.addWidget(delivery_date_edit)
        
        # Comments section
        layout.addWidget(QLabel("Comments (optional):"))
        comments_text = QTextEdit()
        comments_text.setMaximumHeight(80)
        comments_text.setPlaceholderText("Enter any comments that will appear in the packing list header...")
        layout.addWidget(comments_text)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            cursor.close()
            conn.close()
            return
        
        # Get values from dialog
        delivery_date = delivery_date_edit.date().toPyDate()
        comments = comments_text.toPlainText().strip()
        
        try:
            # Generate packing list serial number
            packing_list_serial = self.generate_serial_number("PL")
            
            # Create packing list
            cursor.execute("""
                INSERT INTO packing_lists (packing_list_serial, customer_id, created_at, delivery_date, total_records, total_items, comments) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (packing_list_serial, customer_id, datetime.now(), delivery_date, len(stitching_ids), 0, comments))
            packing_list_id = cursor.lastrowid
            
            # Link stitching records to packing list
            for sid in stitching_ids:
                cursor.execute("INSERT INTO packing_list_lines (packing_list_id, stitching_invoice_id) VALUES (%s, %s)", 
                             (packing_list_id, sid))
            
            # Calculate total items - use safer approach to handle malformed JSON
            cursor.execute("""
                SELECT s.size_qty_json
                FROM stitching_invoices s
                WHERE s.id IN ({})
            """.format(','.join(['%s'] * len(stitching_ids))), tuple(stitching_ids))
            
            total_items = 0
            for row in cursor.fetchall():
                try:
                    if row['size_qty_json']:
                        size_qty = eval(row['size_qty_json']) if isinstance(row['size_qty_json'], str) else row['size_qty_json']
                        if isinstance(size_qty, dict):
                            total_items += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
                except Exception as e:
                    logger.warning(f"Could not parse size_qty_json for stitching invoice: {e}")
                    continue
            
            # Update total items and save comments
            cursor.execute("UPDATE packing_lists SET total_items = %s, comments = %s WHERE id = %s", (total_items, comments, packing_list_id))
            
            conn.commit()
            # Log audit action for packing list creation
            log_audit_action(
                user=self.current_user,
                action_type="CREATE",
                entity="PackingList",
                entity_id=packing_list_id,
                description=f"Created packing list {packing_list_serial} with {len(stitching_ids)} records.",
                details={"packing_list_serial": packing_list_serial, "stitching_ids": stitching_ids, "comments": comments}
            )
            QMessageBox.information(self, "Success", f"Packing list {packing_list_serial} created with {len(stitching_ids)} records and {total_items} items.")
            
            # Generate PDF without garment cost and don't open automatically
            self.generate_grouped_packing_list_pdf(packing_list_id, view_after=False, comments=comments, show_garment_cost=False)
            
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="PackingList",
                entity_id=None,
                description=f"Error creating packing list: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            logger.error(f"Error creating packing list: {e}")
            QMessageBox.critical(self, "Error", f"Could not create packing list: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        
        # Refresh the packing list table
        self.refresh_packing_list_table()
        self.refresh_stitching_lines_table()

    def generate_grouped_packing_list_pdf(self, packing_list_id, view_after=False, comments=None, show_garment_cost=False):
        # Debug logging
        logger.info(f"Generating packing list PDF for ID {packing_list_id}, show_garment_cost: {show_garment_cost}")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get packing list details (including comments)
        cursor.execute('''
            SELECT pl.packing_list_serial, c.short_name as customer, pl.created_at, pl.delivery_date, pl.total_records, pl.total_items, pl.comments
            FROM packing_lists pl
            LEFT JOIN customers c ON pl.customer_id = c.id
            WHERE pl.id=%s
        ''', (packing_list_id,))
        packing_list = cursor.fetchone()
        if packing_list is None:
            cursor.close()
            conn.close()
            QMessageBox.critical(self, "Error", "Could not find packing list for PDF generation.")
            return
        comments = str(packing_list.get('comments', ''))
        
        # Get all stitching records in this packing list with fabric unit price
        cursor.execute('''
            SELECT s.*, l.color, i.invoice_number, i.invoice_date, l.item_name as fabric_name, l.unit_price as fabric_unit_price, l.delivery_note
            FROM packing_list_lines pll
            JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id
            LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
            LEFT JOIN invoices i ON l.invoice_id = i.id
            WHERE pll.packing_list_id=%s
        ''', (packing_list_id,))
        lines = cursor.fetchall()
        
        # Debug: Check if we have the required data for cost calculation
        if show_garment_cost:
            logger.info(f"Checking data for {len(lines)} lines")
            for i, line in enumerate(lines):
                fabric_used = line.get('yard_consumed', 0) or 0
                fabric_price = line.get('fabric_unit_price', 0) or 0
                sewing_price = line.get('price', 0) or 0
                logger.info(f"Line {i}: fabric_used={fabric_used}, fabric_price={fabric_price}, sewing_price={sewing_price}")
        
        # Fetch image paths for all image_ids
        image_map = {}
        image_ids = [line['image_id'] for line in lines if line.get('image_id')]
        if image_ids:
            format_ids = ','.join(['%s']*len(image_ids))
            cursor2 = conn.cursor(dictionary=True)
            cursor2.execute(f"SELECT id, file_path FROM images WHERE id IN ({format_ids})", tuple(image_ids))
            for row in cursor2.fetchall():
                image_map[row['id']] = row['file_path']
            cursor2.close()
        
        cursor.close()
        conn.close()
        
        # Generate PDF
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        
        # Professional Company Header
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "M.S.K Textile Trading", ln=1, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, "Professional Garment Manufacturing & Trading", ln=1, align='C')
        pdf.ln(5)
        
        # Packing List Header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, "PACKING LIST", ln=1, align='C')
        pdf.ln(2)
        
        # Header Information
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Packing List #:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, packing_list['packing_list_serial'], 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Date:", 0)
        pdf.set_font("Arial", '', 10)
        # Use delivery_date if available, otherwise fall back to created_at
        display_date = packing_list.get('delivery_date') or packing_list['created_at']
        pdf.cell(50, 6, format_ddmmyy(display_date), ln=1)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Customer:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, packing_list['customer'], 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Total SKU:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, str(len(lines)), 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Total Quantity:", 0)
        pdf.set_font("Arial", '', 10)
        total_qty_delivered = sum(
            sum(eval(line.get('size_qty_json', '{}')).get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            for line in lines if line.get('size_qty_json')
        )
        pdf.cell(50, 6, str(total_qty_delivered), ln=1)
        
        # Comments Section
        if comments:
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Comments:", ln=1)
            pdf.set_font("Arial", '', 9)
            # Wrap comments to fit page width
            comment_lines = []
            words = comments.split()
            current_line = ""
            for word in words:
                if pdf.get_string_width(current_line + " " + word) < 180:  # Page width minus margins
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        comment_lines.append(current_line)
                    current_line = word
            if current_line:
                comment_lines.append(current_line)
            
            for line in comment_lines:
                pdf.cell(0, 5, line, ln=1)
        
        pdf.ln(5)
        
        # Table Header
        pdf.set_font("Arial", 'B', 8)
        col_widths = [22, 16, 25, 20, 12, 12, 12, 12, 12, 12, 15, 12]
        if show_garment_cost:
            col_widths.append(20)  # Add column for garment cost
            logger.info(f"Added cost column, total columns: {len(col_widths)}")
        
        # Adjust column widths to fit page
        total_width = sum(col_widths)
        if total_width > 190:  # Page width minus margins
            scale_factor = 190 / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        headers = ["Serial #", "Image", "Garment", "Fabric", "Color", "S", "M", "L", "XL", "XXL", "XXXL", "Total"]
        if show_garment_cost:
            headers.append("Cost (Inc Vat)")
            logger.info("Added 'Cost (Inc Vat)' header")
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
        pdf.ln()
        
        # Table Content
        pdf.set_font("Arial", '', 7)
        for line_idx, line in enumerate(lines):
            # Serial #
            pdf.cell(col_widths[0], 18, str(line['stitching_invoice_number'] or ''), 1, 0, 'C')
            
            # Image
            img_path = image_map.get(line.get('image_id'))
            x = pdf.get_x()
            y = pdf.get_y()
            if img_path and os.path.exists(img_path):
                pdf.cell(col_widths[1], 18, '', 1, 0)
                pdf.image(img_path, x+1, y+1, col_widths[1]-2, 16)
            else:
                pdf.cell(col_widths[1], 18, '', 1, 0)
            pdf.set_xy(x+col_widths[1], y)
            
            # Garment
            pdf.cell(col_widths[2], 18, str(line['stitched_item'] or ''), 1, 0, 'C')
            
            # Fabric
            pdf.cell(col_widths[3], 18, str(line['fabric_name'] or ''), 1, 0, 'C')
            
            # Color
            pdf.cell(col_widths[4], 18, str(line['color'] or ''), 1, 0, 'C')
            
            # Size quantities
            try:
                size_qty = eval(line['size_qty_json']) if line['size_qty_json'] else {}
            except Exception:
                size_qty = {}
            
            for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                pdf.cell(col_widths[5 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)], 18, str(size_qty.get(sz, 0)), 1, 0, 'C')
            
            # Total quantity
            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            pdf.cell(col_widths[11], 18, str(total_qty), 1, 0, 'C')
            
            # Garment cost (if enabled) - using enhanced calculation including all fabrics
            if show_garment_cost:
                total_garments = total_qty
                
                if total_garments > 0:
                    # Use the enhanced calculate_garment_cost_per_piece function
                    total_cost_per_garment = self.calculate_garment_cost_per_piece(line, total_garments)
                    cost_text = f"{total_cost_per_garment:.2f}"
                    
                    logger.info(f"Line {line_idx}: cost_per_garment={cost_text}")
                    pdf.cell(col_widths[12], 18, cost_text, 1, 0, 'C')
                else:
                    logger.info(f"Line {line_idx}: No garments, showing 0.00")
                    pdf.cell(col_widths[12], 18, "0.00", 1, 0, 'C')
            
            pdf.ln(18)
            
            # Add cost breakdown under each line if garment cost is enabled
            if show_garment_cost and total_qty > 0:
                # Get all fabric costs using the enhanced calculation
                main_fabric_used = line.get('yard_consumed', 0) or 0
                main_fabric_price = line.get('fabric_unit_price', 0) or 0
                main_fabric_cost = float(main_fabric_used) * float(main_fabric_price)
                
                # Get multi-fabric costs
                multi_fabric_cost = 0
                multi_fabrics_list = []
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT gf.*, l.item_name, l.color, i.invoice_number
                        FROM garment_fabrics gf
                        JOIN invoice_lines l ON gf.fabric_invoice_line_id = l.id
                        JOIN invoices i ON l.invoice_id = i.id
                        WHERE gf.stitching_invoice_id = %s
                        ORDER BY l.item_name, l.color
                    """, (line['id'],))
                    multi_fabrics = cursor.fetchall()
                    for fabric in multi_fabrics:
                        multi_fabric_cost += float(fabric['total_fabric_cost'])
                        multi_fabrics_list.append(fabric)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    logger.warning(f"Could not fetch multi-fabric costs: {e}")
                
                # Get lining fabric costs
                lining_cost = 0
                lining_fabrics_list = []
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT * FROM lining_fabrics 
                        WHERE stitching_invoice_id = %s
                        ORDER BY lining_name
                    """, (line['id'],))
                    lining_fabrics = cursor.fetchall()
                    for lining in lining_fabrics:
                        lining_cost += float(lining['total_cost'])
                        lining_fabrics_list.append(lining)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    logger.warning(f"Could not fetch lining costs: {e}")
                
                # Calculate total fabric cost
                total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
                fabric_cost_per_garment = total_fabric_cost / total_qty
                
                # Calculate sewing cost with VAT if applicable
                sewing_price = line.get('price', 0) or 0
                if line.get('add_vat'):
                    base_sewing_cost = float(sewing_price)
                    vat_amount = base_sewing_cost * 0.07
                    sewing_cost_per_garment = base_sewing_cost + vat_amount
                else:
                    sewing_cost_per_garment = float(sewing_price)
                
                total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
                
                thb_str = "THB "
                thb = thb_str

                # Compact cost breakdown text
                pdf.set_font("Arial", '', 5)
                pdf.cell(0, 3, f"Cost Breakdown for {line['stitched_item']}:", ln=1)
                
                # Main fabric breakdown
                if main_fabric_used > 0 and main_fabric_price > 0:
                    yards_per_piece = main_fabric_used/total_qty
                    cost_per_piece = main_fabric_cost/total_qty
                    pdf.cell(0, 2, f"  Main: {line.get('fabric_name', '')} ({line.get('color', '')}) - {main_fabric_used:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{main_fabric_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
                
                # Multi-fabric breakdown
                if multi_fabrics_list:
                    for fabric in multi_fabrics_list:
                        consumption = fabric['consumption_yards']
                        unit_price = fabric['unit_price']
                        total_cost = fabric['total_fabric_cost']
                        yards_per_piece = consumption/total_qty
                        cost_per_piece = total_cost/total_qty
                        pdf.cell(0, 2, f"  Add: {fabric['item_name']} ({fabric['color']}) - {consumption:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{unit_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
                
                # Lining fabric breakdown
                if lining_fabrics_list:
                    for lining in lining_fabrics_list:
                        consumption = lining['consumption_yards']
                        unit_price = lining['unit_price']
                        total_cost = lining['total_cost']
                        yards_per_piece = consumption/total_qty
                        cost_per_piece = total_cost/total_qty
                        pdf.cell(0, 2, f"  Lining: {lining['lining_name']} - {consumption:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{unit_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
                
                # Summary
                pdf.cell(0, 2, f"  Fabric Total: {thb}{fabric_cost_per_garment:.2f}/pc", ln=1)
                
                # Stitching cost
                if line.get('add_vat'):
                    base_sewing_cost = float(sewing_price)
                    vat_amount = base_sewing_cost * 0.07
                    total_sewing_cost = base_sewing_cost + vat_amount
                    pdf.cell(0, 2, f"  Stitching: {thb}{base_sewing_cost:.2f} + {thb}{vat_amount:.2f} VAT = {thb}{total_sewing_cost:.2f}/pc", ln=1)
                else:
                    pdf.cell(0, 2, f"  Stitching: {thb}{sewing_price:.2f}/pc", ln=1)
                
                pdf.cell(0, 2, f"  Total: {thb}{total_cost_per_garment:.2f}/pc", ln=1)
                pdf.ln(1)
        
        # Footer - removed total quantity and total garment cost as requested
        # Only show if there are no cost breakdowns to avoid redundancy
        if not show_garment_cost:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, f"Total Quantity Delivered: {total_qty_delivered}", ln=1)
        
        # Save PDF
        safe_serial = packing_list['packing_list_serial'].replace('/', '_')
        dir_path = os.path.join('packing_lists', safe_serial)
        os.makedirs(dir_path, exist_ok=True)
        pdf_name = f"{packing_list['packing_list_serial']}.pdf"
        out_path = os.path.join(dir_path, pdf_name)
        pdf.output(out_path)
        
        logger.info(f"PDF saved to: {out_path}")
        
        if view_after:
            self.open_pdf_system(out_path)
        else:
            QMessageBox.information(self, "PDF Generated", f"Packing List PDF saved as {out_path}")

    def delete_stitching_record(self):
        """Delete selected stitching record and revert fabric inventory changes"""
        selected_items = self.stitching_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more stitching records to delete.")
            return
        
        # Filter to only parent items (stitching records), not child fabrics
        parent_items = [item for item in selected_items if item.parent() is None]
        if not parent_items:
            QMessageBox.information(self, "No Selection", "Please select stitching records, not fabric details.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete {len(parent_items)} stitching record(s)?\n\nThis will:\n• Revert fabric inventory changes\n• Remove associated images\n• Remove from packing lists (if any)\n• Remove from group bills (if any)\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            deleted_count = 0
            errors = []
            
            for item in parent_items:
                try:
                    # Get stitching record details
                    stitching_id = item.data(0, Qt.ItemDataRole.UserRole)
                    serial = item.text(1)  # Serial # is col 1
                    cursor.execute("""
                        SELECT s.*, l.yards_consumed, l.item_name as fabric_name
                        FROM stitching_invoices s
                        LEFT JOIN invoice_lines l ON s.invoice_line_id = l.id
                        WHERE s.stitching_invoice_number = %s
                    """, (serial,))
                    record = cursor.fetchone()
                    
                    if not record:
                        errors.append(f"Record {serial}: Not found in database")
                        continue
                    
                    # Check if stitching record is included in any packing lists
                    cursor.execute("""
                        SELECT pl.packing_list_serial, pl.created_at
                        FROM packing_list_lines pll
                        JOIN packing_lists pl ON pll.packing_list_id = pl.id
                        WHERE pll.stitching_invoice_id = %s
                    """, (record['id'],))
                    packing_lists = cursor.fetchall()
                    
                    if packing_lists:
                        packing_list_names = [pl['packing_list_serial'] for pl in packing_lists]
                        errors.append(f"Record {serial}: Cannot delete - included in packing list(s): {', '.join(packing_list_names)}")
                        continue
                    
                    # Start transaction for this record
                    cursor.execute("START TRANSACTION")
                    
                    # 1. Revert fabric inventory changes
                    if record.get('yard_consumed') and record.get('fabric_name'):
                        cursor.execute("""
                            UPDATE fabric_inventory 
                            SET total_consumed = total_consumed - %s,
                                pending_amount = pending_amount + %s
                            WHERE item_name = %s
                        """, (record['yard_consumed'], record['yard_consumed'], record['fabric_name']))
                        
                        # If no rows affected, create inventory entry
                        if cursor.rowcount == 0:
                            cursor.execute("""
                                INSERT INTO fabric_inventory (item_name, total_delivered, total_consumed, total_defective, pending_amount)
                                VALUES (%s, 0, 0, 0, %s)
                            """, (record['fabric_name'], record['yard_consumed']))
                    
                    # 2. Remove from packing_list_lines
                    cursor.execute("DELETE FROM packing_list_lines WHERE stitching_invoice_id = %s", (record['id'],))
                    
                    # 3. Remove from stitching_invoice_group_lines
                    cursor.execute("DELETE FROM stitching_invoice_group_lines WHERE stitching_invoice_id = %s", (record['id'],))
                    
                    # 4. Set billing_group_id to NULL
                    cursor.execute("UPDATE stitching_invoices SET billing_group_id = NULL WHERE id = %s", (record['id'],))
                    
                    # 5. Delete associated image file and database entry
                    if record.get('image_id'):
                        # Get image file path
                        cursor.execute("SELECT file_path FROM images WHERE id = %s", (record['image_id'],))
                        image_record = cursor.fetchone()
                        if image_record and image_record['file_path']:
                            try:
                                if os.path.exists(image_record['file_path']):
                                    os.remove(image_record['file_path'])
                                    logger.info(f"Deleted image file: {image_record['file_path']}")
                            except Exception as e:
                                logger.warning(f"Could not delete image file {image_record['file_path']}: {e}")
                        
                        # Set image_id to NULL in stitching record first
                        cursor.execute("UPDATE stitching_invoices SET image_id = NULL WHERE id = %s", (record['id'],))
                        
                        # Delete image database entry
                        cursor.execute("DELETE FROM images WHERE id = %s", (record['image_id'],))
                    
                    # 6. Revert secondary fabric consumption from garment_fabrics BEFORE deleting them
                    cursor.execute("""
                        SELECT gf.fabric_invoice_line_id, gf.consumption_yards
                        FROM garment_fabrics gf
                        WHERE gf.stitching_invoice_id = %s
                    """, (record['id'],))
                    secondary_fabrics = cursor.fetchall()
                    
                    for secondary_fabric in secondary_fabrics:
                        # Revert consumption in invoice_lines
                        cursor.execute("""
                            UPDATE invoice_lines 
                            SET yards_consumed = yards_consumed - %s 
                            WHERE id = %s
                        """, (secondary_fabric['consumption_yards'], secondary_fabric['fabric_invoice_line_id']))
                    
                    # 7. Revert fabric consumed in invoice line
                    if record.get('yard_consumed') and record.get('invoice_line_id'):
                        cursor.execute("""
                            UPDATE invoice_lines 
                            SET yards_consumed = yards_consumed - %s 
                            WHERE id = %s
                        """, (record['yard_consumed'], record['invoice_line_id']))
                    
                    # 8. Delete child records (garment_fabrics and lining_fabrics) before parent
                    cursor.execute("DELETE FROM garment_fabrics WHERE stitching_invoice_id = %s", (record['id'],))
                    cursor.execute("DELETE FROM lining_fabrics WHERE stitching_invoice_id = %s", (record['id'],))
                    
                    # 9. Delete stitching record
                    cursor.execute("DELETE FROM stitching_invoices WHERE id = %s", (record['id'],))
                    
                    # Commit transaction for this record
                    cursor.execute("COMMIT")
                    deleted_count += 1
                    
                    logger.info(f"Successfully deleted stitching record {serial}")
                    
                except Exception as e:
                    # Rollback transaction for this record
                    cursor.execute("ROLLBACK")
                    error_msg = f"Record {serial}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Error deleting stitching record {serial}: {e}")
                    continue
            
            conn.close()
            
            # Show results
            if deleted_count > 0:
                success_msg = f"Successfully deleted {deleted_count} stitching record(s)."
                if errors:
                    success_msg += f"\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.information(self, "Delete Complete", success_msg)
            else:
                error_msg = "No records were deleted.\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.critical(self, "Delete Failed", error_msg)
            
            # Refresh all tables
            self.refresh_stitching_lines_table()
            self.refresh_packing_list_table()
            self.refresh_group_bill_table()
            
        except Exception as e:
            logger.error(f"Error in delete_stitching_record: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting records: {e}")

    def delete_packing_list(self):
        """Delete selected packing list and ungroup stitching records"""
        selected_items = self.packing_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more packing lists to delete.")
            return
        
        # Get packing list IDs from selected items (only parent items, not child stitching records)
        packing_list_ids = []
        for item in selected_items:
            if item.parent() is None:  # Only parent items (packing lists)
                packing_list_id = item.data(0, Qt.ItemDataRole.UserRole)
                if packing_list_id:
                    packing_list_ids.append(packing_list_id)
        
        if not packing_list_ids:
            QMessageBox.information(self, "No Selection", "Please select packing lists (not individual stitching records) to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete {len(packing_list_ids)} packing list(s)?\n\nThis will:\n• Remove stitching records from packing lists\n• Delete packing list PDFs\n• Update stitching records to show as 'In-Stock'\n• Update group bills (if any contain these records)\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            deleted_count = 0
            errors = []
            
            for packing_list_id in packing_list_ids:
                try:
                    # Get packing list details
                    cursor.execute("""
                        SELECT pl.*, c.short_name as customer_name
                        FROM packing_lists pl
                        LEFT JOIN customers c ON pl.customer_id = c.id
                        WHERE pl.id = %s
                    """, (packing_list_id,))
                    packing_list = cursor.fetchone()
                    
                    if not packing_list:
                        errors.append(f"Packing list ID {packing_list_id}: Not found in database")
                        continue
                    
                    # Start transaction for this packing list
                    cursor.execute("START TRANSACTION")
                    
                    # 1. Get all stitching records in this packing list
                    cursor.execute("""
                        SELECT pll.stitching_invoice_id, s.stitching_invoice_number
                        FROM packing_list_lines pll
                        JOIN stitching_invoices s ON pll.stitching_invoice_id = s.id
                        WHERE pll.packing_list_id = %s
                    """, (packing_list_id,))
                    stitching_records = cursor.fetchall()
                    
                    # 2. Remove from packing_list_lines
                    cursor.execute("DELETE FROM packing_list_lines WHERE packing_list_id = %s", (packing_list_id,))
                    
                    # 3. Update group bills that contain these stitching records
                    for record in stitching_records:
                        # Check if this stitching record is in any group bill
                        cursor.execute("""
                            SELECT sigl.group_id, sig.group_number
                            FROM stitching_invoice_group_lines sigl
                            JOIN stitching_invoice_groups sig ON sigl.group_id = sig.id
                            WHERE sigl.stitching_invoice_id = %s
                        """, (record['stitching_invoice_id'],))
                        group_records = cursor.fetchall()
                        
                        for group_record in group_records:
                            # Remove from group
                            cursor.execute("DELETE FROM stitching_invoice_group_lines WHERE group_id = %s AND stitching_invoice_id = %s", 
                                         (group_record['group_id'], record['stitching_invoice_id']))
                            
                            # Set billing_group_id to NULL
                            cursor.execute("UPDATE stitching_invoices SET billing_group_id = NULL WHERE id = %s", 
                                         (record['stitching_invoice_id'],))
                            
                            logger.info(f"Removed stitching record {record['stitching_invoice_number']} from group {group_record['group_number']}")
                    
                    # 4. Delete packing list PDF files
                    packing_list_serial = packing_list['packing_list_serial']
                    if packing_list_serial:
                        safe_serial = packing_list_serial.replace('/', '_')
                        pdf_dir = os.path.join('packing_lists', safe_serial)
                        pdf_file = os.path.join(pdf_dir, f"{packing_list_serial}.pdf")
                        
                        try:
                            if os.path.exists(pdf_file):
                                os.remove(pdf_file)
                                logger.info(f"Deleted packing list PDF: {pdf_file}")
                            
                            # Try to remove directory if empty
                            if os.path.exists(pdf_dir) and not os.listdir(pdf_dir):
                                os.rmdir(pdf_dir)
                                logger.info(f"Removed empty directory: {pdf_dir}")
                        except Exception as e:
                            logger.warning(f"Could not delete PDF file {pdf_file}: {e}")
                    
                    # 5. Delete packing list from database
                    cursor.execute("DELETE FROM packing_lists WHERE id = %s", (packing_list_id,))
                    
                    # Commit transaction for this packing list
                    cursor.execute("COMMIT")
                    deleted_count += 1
                    
                    logger.info(f"Successfully deleted packing list {packing_list_serial} with {len(stitching_records)} stitching records")
                    # Log audit action for packing list deletion
                    log_audit_action(
                        user=self.current_user,
                        action_type="DELETE",
                        entity="PackingList",
                        entity_id=packing_list_id,
                        description=f"Deleted packing list {packing_list_serial} with {len(stitching_records)} stitching records.",
                        details={"packing_list_serial": packing_list_serial, "stitching_records": stitching_records, "customer_name": packing_list.get('customer_name', '')}
                    )
                    
                except Exception as e:
                    log_audit_action(
                        user=getattr(self, 'current_user', None),
                        action_type="ERROR",
                        entity="PackingList",
                        entity_id=packing_list_id,
                        description=f"Error deleting packing list: {str(e)}",
                        details={"traceback": traceback.format_exc()}
                    )
                    # Rollback transaction for this packing list
                    cursor.execute("ROLLBACK")
                    error_msg = f"Packing list ID {packing_list_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Error deleting packing list {packing_list_id}: {e}")
                    continue
            
            conn.close()
            
            # Show results
            if deleted_count > 0:
                success_msg = f"Successfully deleted {deleted_count} packing list(s)."
                if errors:
                    success_msg += f"\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.information(self, "Delete Complete", success_msg)
            else:
                error_msg = "No packing lists were deleted.\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.critical(self, "Delete Failed", error_msg)
            
            # Refresh all tables
            self.refresh_packing_list_table()
            self.refresh_stitching_lines_table()
            self.refresh_group_bill_table()
            
        except Exception as e:
            logger.error(f"Error in delete_packing_list: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting packing lists: {e}")

    def delete_group_bill(self):
        """Delete selected group bill and ungroup packing lists"""
        selected_items = self.gb_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more group bills to delete.")
            return
        
        # Get group bill IDs from selected items (only parent items, not child invoices)
        group_bill_ids = []
        for item in selected_items:
            if item.parent() is None:  # Only parent items (group bills)
                group_id = item.data(0, Qt.ItemDataRole.UserRole)
                if group_id:
                    group_bill_ids.append(group_id)
        
        if not group_bill_ids:
            QMessageBox.information(self, "No Selection", "Please select group bills (not individual invoices) to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete {len(group_bill_ids)} group bill(s)?\n\nThis will:\n• Remove stitching records from group bills\n• Delete group bill PDFs\n• Update stitching records to show as 'Unbilled'\n• Update packing lists to show as 'Unbilled'\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            deleted_count = 0
            errors = []
            
            for group_id in group_bill_ids:
                try:
                    # Get group bill details
                    cursor.execute("""
                        SELECT sig.*, c.short_name as customer_name
                        FROM stitching_invoice_groups sig
                        LEFT JOIN customers c ON sig.customer_id = c.id
                        WHERE sig.id = %s
                    """, (group_id,))
                    group_bill = cursor.fetchone()
                    
                    if not group_bill:
                        errors.append(f"Group bill ID {group_id}: Not found in database")
                        continue
                    
                    # Start transaction for this group bill
                    cursor.execute("START TRANSACTION")
                    
                    # 1. Get all stitching records in this group bill
                    cursor.execute("""
                        SELECT sigl.stitching_invoice_id, s.stitching_invoice_number
                        FROM stitching_invoice_group_lines sigl
                        JOIN stitching_invoices s ON sigl.stitching_invoice_id = s.id
                        WHERE sigl.group_id = %s
                    """, (group_id,))
                    stitching_records = cursor.fetchall()
                    
                    # 2. Remove from stitching_invoice_group_lines
                    cursor.execute("DELETE FROM stitching_invoice_group_lines WHERE group_id = %s", (group_id,))
                    
                    # 3. Set billing_group_id to NULL for all stitching records in this group
                    cursor.execute("UPDATE stitching_invoices SET billing_group_id = NULL WHERE billing_group_id = %s", (group_id,))
                    
                    # 4. Delete group bill PDF files
                    group_number = group_bill['group_number']
                    if group_number:
                        safe_group_number = group_number.replace('/', '_')
                        group_dir = os.path.join('group_bills', safe_group_number)
                        
                        try:
                            # Delete all PDF files in the group directory
                            if os.path.exists(group_dir):
                                for filename in os.listdir(group_dir):
                                    if filename.endswith('.pdf'):
                                        pdf_file = os.path.join(group_dir, filename)
                                        os.remove(pdf_file)
                                        logger.info(f"Deleted group bill PDF: {pdf_file}")
                                
                                # Try to remove directory if empty
                                if not os.listdir(group_dir):
                                    os.rmdir(group_dir)
                                    logger.info(f"Removed empty directory: {group_dir}")
                        except Exception as e:
                            logger.warning(f"Could not delete PDF files in {group_dir}: {e}")
                    
                    # 5. Delete group bill from database
                    cursor.execute("DELETE FROM stitching_invoice_groups WHERE id = %s", (group_id,))
                    
                    # Commit transaction for this group bill
                    cursor.execute("COMMIT")
                    deleted_count += 1
                    
                    logger.info(f"Successfully deleted group bill {group_number} with {len(stitching_records)} stitching records")
                    # Log audit action for group bill deletion
                    log_audit_action(
                        user=self.current_user,
                        action_type="DELETE",
                        entity="GroupBill",
                        entity_id=group_id,
                        description=f"Deleted group bill {group_number} with {len(stitching_records)} stitching records.",
                        details={"group_number": group_number, "stitching_records": stitching_records, "customer_name": group_bill.get('customer_name', '')}
                    )
                    
                except Exception as e:
                    log_audit_action(
                        user=getattr(self, 'current_user', None),
                        action_type="ERROR",
                        entity="GroupBill",
                        entity_id=group_id,
                        description=f"Error deleting group bill: {str(e)}",
                        details={"traceback": traceback.format_exc()}
                    )
                    # Rollback transaction for this group bill
                    cursor.execute("ROLLBACK")
                    error_msg = f"Group bill ID {group_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Error deleting group bill {group_id}: {e}")
                    continue
            
            conn.close()
            
            # Show results
            if deleted_count > 0:
                success_msg = f"Successfully deleted {deleted_count} group bill(s)."
                if errors:
                    success_msg += f"\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.information(self, "Delete Complete", success_msg)
            else:
                error_msg = "No group bills were deleted.\n\nErrors:\n" + "\n".join(errors)
                QMessageBox.critical(self, "Delete Failed", error_msg)
            
            # Refresh all tables
            self.refresh_group_bill_table()
            self.refresh_packing_list_table()
            self.refresh_stitching_lines_table()
            
        except Exception as e:
            logger.error(f"Error in delete_group_bill: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting group bills: {e}")

    def add_customer_id_filter(self):
        cid = self.customer_id_input.text().strip()
        if not cid or cid in self.customer_ids:
            return
        self.customer_ids.append(cid)
        self.save_customer_ids()
        self.update_customer_id_list_widget()
        self.customer_id_input.clear()

    def remove_customer_id_filter(self):
        selected = self.selected_customers_list.selectedItems()
        for item in selected:
            cid = item.text()
            if cid in self.customer_ids:
                self.customer_ids.remove(cid)
        self.save_customer_ids()
        self.update_customer_id_list_widget()

    def clear_all_customer_ids(self):
        self.customer_ids = []
        self.save_customer_ids()
        self.update_customer_id_list_widget()

    def update_customer_id_list_widget(self):
        self.selected_customers_list.clear()
        self.selected_customers_list.addItems(self.customer_ids)

    def get_selected_customer_ids(self):
        """Get list of selected customer IDs from the main customer_ids list"""
        return self.customer_ids.copy()

    def load_customer_ids(self):
        try:
            if os.path.exists(CUSTOMER_ID_FILE):
                with open(CUSTOMER_ID_FILE, 'r') as f:
                    self.customer_ids = json.load(f)
            else:
                self.customer_ids = []
        except Exception as e:
            self.customer_ids = []
            logger.error(f"Failed to load customer IDs: {e}")

    def save_customer_ids(self):
        try:
            with open(CUSTOMER_ID_FILE, 'w') as f:
                json.dump(self.customer_ids, f)
        except Exception as e:
            logger.error(f"Failed to save customer IDs: {e}")

    def open_customer_id_dialog(self):
        self.load_customer_ids()
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Customer IDs")
        dialog.setMinimumWidth(320)
        dialog.setMaximumWidth(340)
        dialog.setMinimumHeight(320)
        dialog.setMaximumHeight(340)
        layout = QVBoxLayout(dialog)
        # Add Customer ID section
        add_customer_row = QHBoxLayout()
        cid_input = QLineEdit()
        cid_input.setPlaceholderText("Enter Customer ID")
        add_customer_row.addWidget(QLabel("Customer ID:"))
        add_customer_row.addWidget(cid_input)
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(60)
        add_customer_row.addWidget(add_btn)
        layout.addLayout(add_customer_row)
        # Selected Customer IDs display (use a local list for the dialog)
        layout.addWidget(QLabel("Selected Customer IDs:"))
        cid_list = QListWidget()
        cid_list.setMaximumHeight(120)
        self.customer_ids.sort()
        cid_list.addItems(self.customer_ids)
        layout.addWidget(cid_list)
        # Remove and clear buttons
        btn_row = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        remove_btn.setFixedWidth(120)
        btn_row.addWidget(remove_btn)
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("background-color: #ff9800; color: white;")
        clear_btn.setFixedWidth(90)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Add/Remove/Clear logic
        def add_cid():
            cid = cid_input.text().strip()
            if not cid:
                return
            # Prevent duplicates
            # Check for duplicates (case-insensitive)
            for i in range(cid_list.count()):
                if cid_list.item(i).text() == cid:
                    QMessageBox.warning(dialog, "Duplicate ID", f"Customer ID '{cid}' already exists.")
                    return
            cid_list.addItem(cid)
            cid_list.sortItems()
            cid_input.clear()
        def remove_selected():
            selected = cid_list.selectedItems()
            for item in selected:
                cid_list.takeItem(cid_list.row(item))
        def clear_all():
            cid_list.clear()
        add_btn.clicked.connect(add_cid)
        remove_btn.clicked.connect(remove_selected)
        clear_btn.clicked.connect(clear_all)
        dialog.exec()
        # After dialog closes, update self.customer_ids and self.selected_customers_list
        self.customer_ids = [cid_list.item(i).text() for i in range(cid_list.count())]
        self.save_customer_ids()
        self.selected_customers_list.clear()
        self.selected_customers_list.addItems(self.customer_ids)
        self.update_customer_id_list_widget()

    def show_login_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Login Required")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Username:"))
        username_input = QLineEdit()
        layout.addWidget(username_input)
        layout.addWidget(QLabel("Password:"))
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_input)
        btn_row = QHBoxLayout()
        login_btn = QPushButton("Login")
        btn_row.addWidget(login_btn)
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        error_label = QLabel()
        error_label.setStyleSheet("color: red;")
        layout.addWidget(error_label)
        def try_login():
            username = username_input.text().strip()
            password = password_input.text()
            if not username or not password:
                error_label.setText("Please enter username and password.")
                return
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s", (username, password_hash))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                self.current_user = user['username']
                self.is_admin = bool(user['is_admin'])
                self.login_btn.setEnabled(False)
                self.logout_btn.setEnabled(True)
                self.enable_main_ui()
                self.update_user_label()
                # Log audit action for successful login
                log_audit_action(
                    user=username,
                    action_type="LOGIN",
                    entity="User",
                    entity_id=username,
                    description=f"User '{username}' logged in.",
                    details={"timestamp": str(datetime.now())}
                )
                dialog.accept()
            else:
                error_label.setText("Invalid username or password.")
                # Log audit action for failed login
                log_audit_action(
                    user=username,
                    action_type="ERROR",
                    entity="User",
                    entity_id=username,
                    description=f"Failed login attempt for user '{username}'.",
                    details={"timestamp": str(datetime.now())}
                )
        login_btn.clicked.connect(try_login)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def logout_user(self):
        # Store the username before clearing it for audit logging
        logged_out_user = self.current_user
        self.current_user = None
        self.is_admin = False
        self.login_btn.setEnabled(True)
        self.logout_btn.setEnabled(False)
        self.disable_main_ui()
        self.update_user_label()
        # Log audit action for logout
        log_audit_action(
            user=logged_out_user,
            action_type="LOGOUT",
            entity="User",
            entity_id=logged_out_user,
            description=f"User '{logged_out_user}' logged out.",
            details={"timestamp": str(datetime.now())}
        )

    def disable_main_ui(self):
        self.stacked.hide()
        self.stacked.setEnabled(False)
        for act in self.actions.values():
            act.setEnabled(False)

    def enable_main_ui(self):
        self.stacked.show()
        self.stacked.setEnabled(True)
        for act in self.actions.values():
            act.setEnabled(True)

    def update_user_label(self):
        if self.current_user:
            self.user_label.setText(f"Logged in as: {self.current_user}")
        else:
            self.user_label.setText("Not logged in")

    def calculate_garment_cost_per_piece(self, row, total_qty):
        """Calculate garment cost per piece including all fabrics (main + multi + lining)"""
        if total_qty <= 0:
            return 0.0
        
        # Get main fabric cost
        fabric_used = row.get('yard_consumed', 0) or 0
        fabric_price = row.get('fabric_unit_price', 0) or 0
        main_fabric_cost = float(fabric_used) * float(fabric_price)
        
        # Get multi-fabric costs
        multi_fabric_cost = 0
        if 'id' in row:  # Only if we have stitching_invoice_id
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT SUM(total_fabric_cost) as total_multi_cost
                    FROM garment_fabrics 
                    WHERE stitching_invoice_id = %s
                """, (row['id'],))
                multi_result = cursor.fetchone()
                if multi_result and multi_result['total_multi_cost']:
                    multi_fabric_cost = float(multi_result['total_multi_cost'])
                cursor.close()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not fetch multi-fabric costs: {e}")
        
        # Get lining fabric costs
        lining_cost = 0
        if 'id' in row:  # Only if we have stitching_invoice_id
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT SUM(total_cost) as total_lining_cost
                    FROM lining_fabrics 
                    WHERE stitching_invoice_id = %s
                """, (row['id'],))
                lining_result = cursor.fetchone()
                if lining_result and lining_result['total_lining_cost']:
                    lining_cost = float(lining_result['total_lining_cost'])
                cursor.close()
                conn.close()
            except Exception as e:
                logger.warning(f"Could not fetch lining costs: {e}")
        
        # Calculate total fabric cost (main + multi + lining)
        total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
        
        # Calculate fabric cost per piece
        fabric_cost_per_garment = total_fabric_cost / total_qty
        
        # Stitching cost per piece (with VAT if applicable)
        sewing_price = row.get('price', 0) or 0
        if row.get('add_vat'):
            base_sewing_cost = float(sewing_price)
            vat_amount = base_sewing_cost * 0.07
            sewing_cost_per_garment = base_sewing_cost + vat_amount
        else:
            sewing_cost_per_garment = float(sewing_price)
        
        # Total cost per piece
        total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
        
        return total_cost_per_garment

    def get_next_serial(self, serial_type):
        """Fetch and increment the last used serial for a given type. Returns the next integer."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT last_value FROM serial_counters WHERE serial_type=%s", (serial_type,))
        row = cursor.fetchone()
        if row:
            next_val = row['last_value'] + 1
            cursor.execute("UPDATE serial_counters SET last_value=%s WHERE serial_type=%s", (next_val, serial_type))
        else:
            next_val = 1
            cursor.execute("INSERT INTO serial_counters (serial_type, last_value) VALUES (%s, %s)", (serial_type, next_val))
        conn.commit()
        cursor.close()
        conn.close()
        return next_val

    def generate_serial_number(self, serial_type):
        """
        Generate unique serial number for any type.
        serial_type: 'ST', 'GB', 'PL', 'GBN'
        Returns: Next available serial number
        """
        now = datetime.now()
        
        if serial_type == "ST":
            # ST/MMYY/XXX format
            mm_yy = now.strftime('%m%y')
            pattern = f"ST/{mm_yy}/%"
            format_string = f"ST/{mm_yy}/{{:03d}}"
            return self._get_next_number("stitching_invoices", "stitching_invoice_number", pattern, format_string)
        
        elif serial_type == "GB":
            # GB/MMYY/XXX format
            mm_yy = now.strftime('%m%y')
            pattern = f"GB/{mm_yy}/%"
            format_string = f"GB/{mm_yy}/{{:03d}}"
            return self._get_next_number("stitching_invoice_groups", "group_number", pattern, format_string)
        
        elif serial_type == "PL":
            # PLYYMMDDXX format
            date_str = now.strftime('%y%m%d')
            pattern = f"PL{date_str}%"
            format_string = f"PL{date_str}{{:02d}}"
            return self._get_next_number("packing_lists", "packing_list_serial", pattern, format_string)
        
        elif serial_type == "GBN":
            # GBNYYMMDDXX format
            date_str = now.strftime('%y%m%d')
            pattern = f"GBN{date_str}%"
            format_string = f"GBN{date_str}{{:02d}}"
            return self._get_next_number("stitching_invoice_groups", "group_number", pattern, format_string)
        
        else:
            raise ValueError(f"Unknown serial type: {serial_type}")

    def _get_next_number(self, table_name, column_name, pattern, format_string):
        """
        Find the next available number for a given pattern.
        Never reuses deleted numbers by finding the highest existing + 1
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all existing serials for this pattern
        cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE {column_name} LIKE %s", (pattern,))
        existing_serials = [row[0] for row in cursor.fetchall()]
        
        # Extract numeric parts
        numbers = []
        for serial in existing_serials:
            try:
                # Extract the numeric part based on the pattern
                if pattern.startswith("ST/") or pattern.startswith("GB/"):
                    # ST/MMYY/XXX or GB/MMYY/XXX format
                    numeric_part = int(serial.split('/')[-1])
                else:
                    # PLYYMMDDXX or GBNYYMMDDXX format
                    numeric_part = int(serial[-2:])
                numbers.append(numeric_part)
            except (ValueError, IndexError):
                continue
        
        # Find next number (start from 1 if no existing numbers)
        next_number = 1 if not numbers else max(numbers) + 1
        
        cursor.close()
        conn.close()
        
        return format_string.format(next_number)

    def assign_tax_invoice_number_packing(self):
        selected_items = self.packing_tree.selectedItems()
        # Only allow assigning to packing lists (parent items)
        packing_list_ids = []
        for item in selected_items:
            if item.parent() is None:  # Only parent items (packing lists)
                packing_list_id = item.data(0, Qt.ItemDataRole.UserRole)
                if packing_list_id:
                    packing_list_ids.append(packing_list_id)
        if not packing_list_ids:
            QMessageBox.information(self, "No Selection", "Please select one or more packing lists (not stitching records) to assign a Tax Invoice Number.")
            return
        # Prompt for Tax Invoice Number
        tax_inv, ok = QInputDialog.getText(self, "Assign Tax Invoice #", "Enter Tax Invoice Number:")
        if not ok or not tax_inv.strip():
            return
        tax_inv = tax_inv.strip()
        # Update in database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if tax_inv == "0":
                cursor.execute(f"UPDATE packing_lists SET tax_invoice_number = NULL WHERE id IN ({','.join(['%s']*len(packing_list_ids))})", tuple(packing_list_ids))
                action_desc = f"Cleared tax invoice number for packing lists: {packing_list_ids}."
            else:
                cursor.execute(f"UPDATE packing_lists SET tax_invoice_number = %s WHERE id IN ({','.join(['%s']*len(packing_list_ids))})", tuple([tax_inv] + packing_list_ids))
                action_desc = f"Assigned tax invoice number '{tax_inv}' to packing lists: {packing_list_ids}."
            conn.commit()
            cursor.close()
            conn.close()
            # Log audit action for packing list tax invoice assignment
            log_audit_action(
                user=self.current_user,
                action_type="UPDATE",
                entity="PackingList",
                entity_id=','.join(str(pid) for pid in packing_list_ids),
                description=action_desc,
                details={"tax_inv": tax_inv if tax_inv != '0' else None, "packing_list_ids": packing_list_ids}
            )
            QMessageBox.information(self, "Success", f"{'Removed' if tax_inv == '0' else 'Assigned'} Tax Invoice # for {len(packing_list_ids)} packing list(s).")
            self.refresh_packing_list_table()
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="PackingList",
                entity_id=','.join(str(pid) for pid in packing_list_ids),
                description=f"Error assigning Tax Invoice #: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            QMessageBox.critical(self, "Error", f"Could not assign Tax Invoice #: {e}")

    def open_add_invoice_line_dialog(self):
        """Open dialog to add a new invoice line item"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Invoice Line Item")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        # Get available customers for dropdown
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, short_name FROM customers ORDER BY short_name")
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Form layout
        form = QFormLayout()
        
        # Customer selection
        customer_combo = QComboBox()
        customer_combo.addItem("Select Customer", None)
        for customer in customers:
            customer_combo.addItem(customer['short_name'], customer['id'])
        form.addRow("Customer:", customer_combo)
        
        # Invoice details
        invoice_number = QLineEdit()
        form.addRow("Invoice Number:", invoice_number)
        
        tax_invoice_number = QLineEdit()
        form.addRow("Tax Invoice Number:", tax_invoice_number)
        
        invoice_date = QDateEdit()
        invoice_date.setDate(QDate.currentDate())
        form.addRow("Invoice Date:", invoice_date)
        
        # Item details
        item_name = QLineEdit()
        form.addRow("Item Name:", item_name)
        
        color = QLineEdit()
        form.addRow("Color:", color)
        
        delivery_note = QLineEdit()
        form.addRow("Delivery Note:", delivery_note)
        
        # Quantities and prices
        yards_sent = QDoubleSpinBox()
        yards_sent.setRange(0, 999999.99)
        yards_sent.setDecimals(2)
        form.addRow("Yards Sent:", yards_sent)
        
        yards_consumed = QDoubleSpinBox()
        yards_consumed.setRange(0, 999999.99)
        yards_consumed.setDecimals(2)
        form.addRow("Yards Consumed:", yards_consumed)
        
        unit_price = QDoubleSpinBox()
        unit_price.setRange(0, 999999.99)
        unit_price.setDecimals(2)
        form.addRow("Unit Price:", unit_price)
        
        delivered_location = QLineEdit()
        form.addRow("Delivered Location:", delivered_location)
        
        layout.addLayout(form)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Validate required fields
            if not customer_combo.currentData():
                QMessageBox.warning(self, "Validation Error", "Please select a customer.")
                return
            if not invoice_number.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter an invoice number.")
                return
            if not item_name.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter an item name.")
                return
            
            # Save to database
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                
                # First, create or get the invoice
                cursor.execute("""
                    SELECT id FROM invoices 
                    WHERE invoice_number = %s AND customer_id = %s
                """, (invoice_number.text().strip(), customer_combo.currentData()))
                
                existing_invoice = cursor.fetchone()
                if existing_invoice:
                    invoice_id = existing_invoice['id']
                    # Update existing invoice
                    cursor.execute("""
                        UPDATE invoices 
                        SET tax_invoice_number = %s, invoice_date = %s
                        WHERE id = %s
                    """, (tax_invoice_number.text().strip(), invoice_date.date().toPyDate(), invoice_id))
                else:
                    # Create new invoice
                    cursor.execute("""
                        INSERT INTO invoices (invoice_number, tax_invoice_number, invoice_date, customer_id)
                        VALUES (%s, %s, %s, %s)
                    """, (invoice_number.text().strip(), tax_invoice_number.text().strip(), 
                          invoice_date.date().toPyDate(), customer_combo.currentData()))
                    invoice_id = cursor.lastrowid
                
                # Create invoice line
                cursor.execute("""
                    INSERT INTO invoice_lines (invoice_id, item_name, color, delivery_note, 
                                             yards_sent, yards_consumed, unit_price, delivered_location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (invoice_id, item_name.text().strip(), color.text().strip(),
                      delivery_note.text().strip(), yards_sent.value(), yards_consumed.value(),
                      unit_price.value(), delivered_location.text().strip()))
                
                # Recalculate and update invoice total
                cursor.execute("""
                    SELECT SUM(unit_price * yards_sent) as total
                    FROM invoice_lines
                    WHERE invoice_id = %s
                """, (invoice_id,))
                total = cursor.fetchone()["total"] or 0
                cursor.execute("""
                    UPDATE invoices SET total_amount = %s WHERE id = %s
                """, (total, invoice_id))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                # Log audit action for invoice line addition
                log_audit_action(
                    user=self.current_user,
                    action_type="CREATE",
                    entity="InvoiceLine",
                    entity_id=invoice_id,
                    description=f"Added invoice line to invoice {invoice_number.text().strip()} for item {item_name.text().strip()}.",
                    details={
                        "invoice_id": invoice_id,
                        "item_name": item_name.text().strip(),
                        "color": color.text().strip(),
                        "delivery_note": delivery_note.text().strip(),
                        "yards_sent": yards_sent.value(),
                        "yards_consumed": yards_consumed.value(),
                        "unit_price": unit_price.value(),
                        "delivered_location": delivered_location.text().strip(),
                        "tax_invoice_number": tax_invoice_number.text().strip(),
                        "invoice_date": str(invoice_date.date().toPyDate()),
                        "customer_id": customer_combo.currentData()
                    }
                )
                QMessageBox.information(self, "Success", "Invoice line item added successfully.")
                self.refresh_invoice_table()
                
            except Exception as e:
                log_audit_action(
                    user=getattr(self, 'current_user', None),
                    action_type="ERROR",
                    entity="InvoiceLine",
                    entity_id=None,
                    description=f"Error saving invoice line: {str(e)}",
                    details={"traceback": traceback.format_exc()}
                )
                QMessageBox.critical(self, "Database Error", f"Error saving invoice line: {str(e)}")
                if conn:
                    conn.rollback()
                    cursor.close()
                    conn.close()

    def delete_invoice_line(self):
        """Delete selected invoice line items"""
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select one or more invoice lines to delete.")
            return
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                   f"Are you sure you want to delete {len(selected_rows)} selected invoice line(s)?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            deleted_count = 0
            deleted_lines = []
            for row in selected_rows:
                # Get the invoice line ID from the hidden column
                id_item = self.invoice_table.item(row.row(), self.invoice_table.columnCount() - 1)
                if not id_item:
                    continue
                invoice_line_id = id_item.text()
                cursor.execute("""
                    SELECT l.id, l.invoice_id, l.item_name, l.color, i.invoice_number
                    FROM invoice_lines l
                    JOIN invoices i ON l.invoice_id = i.id
                    WHERE l.id = %s
                """, (invoice_line_id,))
                line_data = cursor.fetchone()
                if line_data:
                    cursor.execute("DELETE FROM invoice_lines WHERE id = %s", (line_data['id'],))
                    cursor.execute("SELECT COUNT(*) as count FROM invoice_lines WHERE invoice_id = %s", (line_data['invoice_id'],))
                    remaining_lines = cursor.fetchone()['count']
                    if remaining_lines == 0:
                        cursor.execute("DELETE FROM invoices WHERE id = %s", (line_data['invoice_id'],))
                    deleted_count += 1
                    deleted_lines.append({
                        "line_id": line_data['id'],
                        "invoice_id": line_data['invoice_id']
                    })
                    log_audit_action(
                        user=self.current_user,
                        action_type="DELETE",
                        entity="InvoiceLine",
                        entity_id=line_data['id'],
                        description=f"Deleted invoice line for item {line_data['item_name']} from invoice {line_data['invoice_number']}",
                        details={
                            "invoice_number": line_data["invoice_number"],
                            "item_name": line_data["item_name"],
                            "color": line_data["color"]
                        }
                    )
            conn.commit()
            cursor.close()
            conn.close()
            self.refresh_invoice_table()
        except Exception as e:
            log_audit_action(
                user=getattr(self, 'current_user', None),
                action_type="ERROR",
                entity="InvoiceLine",
                entity_id=None,
                description=f"Error deleting invoice line: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            QMessageBox.critical(self, "Database Error", f"Error deleting invoice line: {str(e)}")
            if conn:
                conn.rollback()
                cursor.close()
                conn.close()

    def refresh_audit_log_table(self):
        """Load and display audit log entries from the audit_logs table."""
        self.audit_table.setRowCount(0)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Build query with filters
            query = "SELECT timestamp, user, action_type, entity, entity_id, description, details FROM audit_logs WHERE 1=1"
            params = []
            user_val = self.audit_filter_user.currentText().strip()
            if user_val:
                query += " AND user LIKE %s"
                params.append(f"%{user_val}%")
            action_val = self.audit_filter_action.currentText().strip()
            if action_val:
                query += " AND action_type LIKE %s"
                params.append(f"%{action_val}%")
            entity_val = self.audit_filter_entity.currentText().strip()
            if entity_val:
                query += " AND entity LIKE %s"
                params.append(f"%{entity_val}%")
            date_from = self.audit_filter_date_from.text().strip()
            if date_from:
                try:
                    # Convert DD/MM/YY to YYYY-MM-DD
                    if len(date_from) == 8 and date_from.count('/') == 2:
                        day, month, year = date_from.split('/')
                        # Convert 2-digit year to 4-digit year
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        date_from_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        query += " AND DATE(timestamp) >= %s"
                        params.append(date_from_iso)
                except (ValueError, IndexError):
                    pass
            date_to = self.audit_filter_date_to.text().strip()
            if date_to:
                try:
                    # Convert DD/MM/YY to YYYY-MM-DD
                    if len(date_to) == 8 and date_to.count('/') == 2:
                        day, month, year = date_to.split('/')
                        # Convert 2-digit year to 4-digit year
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        date_to_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        query += " AND DATE(timestamp) <= %s"
                        params.append(date_to_iso)
                except (ValueError, IndexError):
                    pass
            query += " ORDER BY timestamp DESC LIMIT 500"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                row_idx = self.audit_table.rowCount()
                self.audit_table.insertRow(row_idx)
                self.audit_table.setItem(row_idx, 0, QTableWidgetItem(format_ddmmyyhhmm(row['timestamp'])))
                self.audit_table.setItem(row_idx, 1, QTableWidgetItem(str(row['user'] or '')))
                self.audit_table.setItem(row_idx, 2, QTableWidgetItem(str(row['action_type'] or '')))
                self.audit_table.setItem(row_idx, 3, QTableWidgetItem(str(row['entity'] or '')))
                self.audit_table.setItem(row_idx, 4, QTableWidgetItem(str(row['entity_id'] or '')))
                self.audit_table.setItem(row_idx, 5, QTableWidgetItem(str(row['description'] or '')))
                # Details button
                details_btn = QPushButton("View Details")
                details_btn.clicked.connect(lambda checked, details=row['details']: self.show_audit_details_dialog(details))
                self.audit_table.setCellWidget(row_idx, 6, details_btn)
            cursor.close()
            conn.close()
            # Populate filter dropdowns with unique values
            self.populate_audit_log_filters()
        except Exception as e:
            logger.error(f"Error loading audit logs: {e}")

    def show_audit_details_dialog(self, details):
        dialog = QDialog(self)
        dialog.setWindowTitle("Audit Log Details")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        # Pretty print JSON if possible
        try:
            if details:
                parsed = json.loads(details)
                text_edit.setPlainText(json.dumps(parsed, indent=2, ensure_ascii=False))
            else:
                text_edit.setPlainText("(No details)")
        except Exception:
            text_edit.setPlainText(str(details) if details else "(No details)")
        layout.addWidget(text_edit)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        dialog.exec()

    def populate_audit_log_filters(self):
        """Populate filter dropdowns with unique values from audit_logs."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # User
            cursor.execute("SELECT DISTINCT user FROM audit_logs WHERE user IS NOT NULL AND user != '' ORDER BY user")
            users = [row[0] for row in cursor.fetchall() if row[0]]
            self.audit_filter_user.blockSignals(True)
            current = self.audit_filter_user.currentText()
            self.audit_filter_user.clear()
            self.audit_filter_user.addItem("")
            self.audit_filter_user.addItems(users)
            self.audit_filter_user.setCurrentText(current)
            self.audit_filter_user.blockSignals(False)
            # Action
            cursor.execute("SELECT DISTINCT action_type FROM audit_logs WHERE action_type IS NOT NULL AND action_type != '' ORDER BY action_type")
            actions = [row[0] for row in cursor.fetchall() if row[0]]
            self.audit_filter_action.blockSignals(True)
            current = self.audit_filter_action.currentText()
            self.audit_filter_action.clear()
            self.audit_filter_action.addItem("")
            self.audit_filter_action.addItems(actions)
            self.audit_filter_action.setCurrentText(current)
            self.audit_filter_action.blockSignals(False)
            # Entity
            cursor.execute("SELECT DISTINCT entity FROM audit_logs WHERE entity IS NOT NULL AND entity != '' ORDER BY entity")
            entities = [row[0] for row in cursor.fetchall() if row[0]]
            self.audit_filter_entity.blockSignals(True)
            current = self.audit_filter_entity.currentText()
            self.audit_filter_entity.clear()
            self.audit_filter_entity.addItem("")
            self.audit_filter_entity.addItems(entities)
            self.audit_filter_entity.setCurrentText(current)
            self.audit_filter_entity.blockSignals(False)
            
            # Connect filter changes to debounced update
            self.audit_filter_user.currentTextChanged.connect(self.trigger_filter_update)
            self.audit_filter_action.currentTextChanged.connect(self.trigger_filter_update)
            self.audit_filter_entity.currentTextChanged.connect(self.trigger_filter_update)
            self.audit_filter_date_from.textChanged.connect(self.trigger_filter_update)
            self.audit_filter_date_to.textChanged.connect(self.trigger_filter_update)
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error populating audit log filters: {e}")
    
    #Context Menu
    def eventFilter(self, source, event):
        if(event.type() == QtCore.QEvent.Type.MouseButtonPress and
            event.buttons() == QtCore.Qt.MouseButton.RightButton and            
            (source is self.invoice_table.viewport() or source is self.stitching_tree.viewport() or 
             source is self.packing_tree.viewport() or source is self.gb_tree.viewport()
            )):
            '''
            item = self.invoice_table.itemAt(event.pos())
            print('Global Pos:', event.globalPosition())
            if item is not None:
                print('Table Item:', item.row(), item.column())
                self.menu = QMenu(self)
                self.menu.addAction(item.text())         #(QAction('test'))
                #menu.exec_(event.globalPos())
            '''
            self.menu = QMenu(self)
            
            if self.stacked.currentIndex()==0:
                stitchrec_Action = QAction("Create Stitching Record ...",self)
                stitchrec_Action.triggered.connect(self.open_stitching_record_dialog)
                self.menu.addAction(stitchrec_Action)
                
                self.menu.addSeparator()
                
                delloc_Action = QAction("Assign Delivered Location ...", self)
                delloc_Action.triggered.connect(self.assign_delivered_location)
                self.menu.addAction(delloc_Action)
                
                taxinv_Action = QAction("Assign Tax Invoice Number ...",self)
                taxinv_Action.triggered.connect(self.assign_tax_invoice_number)
                self.menu.addAction(taxinv_Action)
                
                self.menu.addSeparator()

                custid_Action = QAction("Customer IDs ...",self)
                custid_Action.triggered.connect(self.open_customer_id_dialog)
                self.menu.addAction(custid_Action)

                self.menu.addSeparator()
                
                addinv_Action = QAction("Add Invoice Line ...",self)
                addinv_Action.triggered.connect(self.open_add_invoice_line_dialog)
                self.menu.addAction(addinv_Action)
                
                delinv_Action = QAction("Delete Selected Invoice ...",self)
                delinv_Action.triggered.connect(self.delete_invoice_line)
                self.menu.addAction(delinv_Action)    
                
                self.menu.addSeparator()
                
                refreshinv_Action = QAction("Refresh",self)
                refreshinv_Action.triggered.connect(self.refresh_invoice_table)
                self.menu.addAction(refreshinv_Action)
                
                # edit invoice quantity
                self.menu.addSeparator()
                
                refreshinv_Action = QAction("Edit Invoice Pending Amount",self)
                refreshinv_Action.triggered.connect(self.open_edit_pending_dialog)
                self.menu.addAction(refreshinv_Action)
                
            elif self.stacked.currentIndex()==1:
                gengroup_Action = QAction("Generate Group Packing List ...", self)
                gengroup_Action.triggered.connect(self.create_grouped_packing_list)
                self.menu.addAction(gengroup_Action)  
                
                self.menu.addSeparator()
                
                delstitch_Action = QAction("Delete Selected Stitching ...",self)
                delstitch_Action.triggered.connect(self.delete_stitching_record)
                self.menu.addAction(delstitch_Action)
                
                self.menu.addSeparator()
                
                refreshstitch_Action = QAction("Refresh",self)
                refreshstitch_Action.triggered.connect(self.refresh_stitching_lines_table)
                self.menu.addAction(refreshstitch_Action)
                
            elif self.stacked.currentIndex()==2:
                createbn_Action = QAction("Group and Create Billing Note ...", self)
                createbn_Action.triggered.connect(self.create_group_billing_note)
                self.menu.addAction(createbn_Action)
                
                self.menu.addSeparator()
                
                viewpack_Action = QAction("View Packing List ...", self)
                viewpack_Action.triggered.connect(self.view_packing_list_pdf_from_tree)
                self.menu.addAction(viewpack_Action)
                
                assigntax_Action = QAction("Assign Tax Invoice # ...", self)
                assigntax_Action.triggered.connect(self.assign_tax_invoice_number_packing)
                self.menu.addAction(assigntax_Action)
                
                self.menu.addSeparator()
                
                delpack_Action = QAction("Delete Selected Packing List ...", self)
                delpack_Action.triggered.connect(self.delete_packing_list)
                self.menu.addAction(delpack_Action)
                
                self.menu.addSeparator()
                
                refreshpack_Action = QAction("Refresh",self)
                refreshpack_Action.triggered.connect(self.refresh_packing_list_table)
                self.menu.addAction(refreshpack_Action)
                
            elif self.stacked.currentIndex()==3:
                viewpdf_Action = QAction("View PDF for Selected Group ...", self)
                viewpdf_Action.triggered.connect(self.on_gb_pdf)
                self.menu.addAction(viewpdf_Action)
                
                self.menu.addSeparator()
                
                refreshgbill_Action = QAction("Delete Selected Group ...",self)
                refreshgbill_Action.triggered.connect(self.delete_group_bill)
                self.menu.addAction(refreshgbill_Action)
                
                self.menu.addSeparator()
                
                refreshgbill_Action = QAction("Refresh",self)
                refreshgbill_Action.triggered.connect(self.refresh_group_bill_table)
                self.menu.addAction(refreshgbill_Action)
                 
        return super(MainWindow, self).eventFilter(source, event)
    
    def generateMenu(self, pos):
        #print("pos======",pos)
        #print("Current Tab======",self.stacked.currentIndex())
        if self.stacked.currentIndex()==0:
            self.menu.exec(self.invoice_table.mapToGlobal(pos))
        elif self.stacked.currentIndex()==1:
            self.menu.exec(self.stitching_tree.mapToGlobal(pos))
        elif self.stacked.currentIndex()==2:
            self.menu.exec(self.packing_tree.mapToGlobal(pos))    
        elif self.stacked.currentIndex()==3:
            self.menu.exec(self.gb_tree.mapToGlobal(pos))   

# --- AUDIT LOGGING HELPER ---
def log_audit_action(user, action_type, entity, entity_id, description, details=None):
    """
    Log an action to the audit_logs table.
    Args:
        user (str or None): Username or None if not logged in
        action_type (str): e.g., CREATE, UPDATE, DELETE, ERROR, LOGIN, etc.
        entity (str): Entity type, e.g., Invoice, PackingList, User
        entity_id (str or int or None): Identifier for the entity (e.g., invoice number, record id)
        description (str): Human-readable summary
        details (str or dict or None): Optional details (will be stringified if dict)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if isinstance(details, dict):
            details_str = json.dumps(details, ensure_ascii=False)
        else:
            details_str = str(details) if details is not None else None
        cursor.execute(
            """
            INSERT INTO audit_logs (user, action_type, entity, entity_id, description, details)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user, action_type, entity, str(entity_id) if entity_id is not None else None, description, details_str)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")

def main():
    app = QApplication(sys.argv)
    apply_dark_material_palette(app)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())

   
if __name__ == "__main__":
    main()
