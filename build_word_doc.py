import zipfile
import html
import os

def create_docx(output_path):
    # XML Document content
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="222222"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:line="276" w:lineRule="auto" w:after="160"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>

  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:pPr>
      <w:spacing w:before="360" w:after="140"/>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:color w:val="0D47A1"/>
      <w:sz w:val="52"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:pPr>
      <w:spacing w:before="0" w:after="300"/>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:rPr>
      <w:color w:val="555555"/>
      <w:sz w:val="26"/>
      <w:i/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:pPr>
      <w:spacing w:before="360" w:after="140"/>
      <w:pBdr>
        <w:bottom w:val="single" w:sz="12" w:space="4" w:color="0D47A1"/>
      </w:pBdr>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:color w:val="0D47A1"/>
      <w:sz w:val="34"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:pPr>
      <w:spacing w:before="260" w:after="100"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:color w:val="1976D2"/>
      <w:sz w:val="28"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:pPr>
      <w:spacing w:before="200" w:after="80"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:color w:val="0288D1"/>
      <w:sz w:val="24"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="ListBullet">
    <w:name w:val="List Bullet"/>
    <w:pPr>
      <w:ind w:left="400" w:hanging="200"/>
      <w:spacing w:before="40" w:after="60"/>
    </w:pPr>
  </w:style>
</w:styles>"""

    # Helper classes for document generation
    paragraphs = []

    def p(text="", bold=False, italic=False, color=None, size=None, align=None, style=None):
        p_elm = ['<w:p>']
        pPr = ['<w:pPr>']
        if style:
            pPr.append(f'<w:pStyle w:val="{style}"/>')
        if align:
            pPr.append(f'<w:jc w:val="{align}"/>')
        pPr.append('</w:pPr>')
        p_elm.append(''.join(pPr))

        if text:
            r_elm = ['<w:r>']
            rPr = ['<w:rPr>']
            if bold:
                rPr.append('<w:b/>')
            if italic:
                rPr.append('<w:i/>')
            if color:
                rPr.append(f'<w:color w:val="{color}"/>')
            if size:
                rPr.append(f'<w:sz w:val="{size}"/>')
            rPr.append('</w:rPr>')
            r_elm.append(''.join(rPr))
            r_elm.append(f'<w:t xml:space="preserve">{html.escape(text)}</w:t>')
            r_elm.append('</w:r>')
            p_elm.append(''.join(r_elm))

        p_elm.append('</w:p>')
        paragraphs.append(''.join(p_elm))

    def bullet(bold_prefix, text):
        p_elm = ['<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr>']
        p_elm.append('<w:r><w:rPr><w:color w:val="0D47A1"/><w:b/></w:rPr><w:t>&#x2022; </w:t></w:r>')
        if bold_prefix:
            p_elm.append(f'<w:r><w:rPr><w:b/><w:color w:val="1E293B"/></w:rPr><w:t xml:space="preserve">{html.escape(bold_prefix)}: </w:t></w:r>')
        p_elm.append(f'<w:r><w:rPr><w:color w:val="334155"/></w:rPr><w:t xml:space="preserve">{html.escape(text)}</w:t></w:r>')
        p_elm.append('</w:p>')
        paragraphs.append(''.join(p_elm))

    def table(rows, col_widths=None):
        t_elm = ['<w:tbl>']
        t_elm.append("""<w:tblPr>
          <w:tblW w:w="9400" w:type="dxa"/>
          <w:jc w:val="center"/>
          <w:tblBorders>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
            <w:left w:val="none"/>
            <w:bottom w:val="single" w:sz="8" w:space="0" w:color="94A3B8"/>
            <w:right w:val="none"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
            <w:insideV w:val="none"/>
          </w:tblBorders>
        </w:tblPr>""")

        for r_idx, row in enumerate(rows):
            is_header = (r_idx == 0)
            t_elm.append('<w:tr>')
            for c_idx, cell in enumerate(row):
                width = col_widths[c_idx] if col_widths and c_idx < len(col_widths) else 2000
                bg_color = '0D47A1' if is_header else ('F8FAFC' if r_idx % 2 == 1 else 'FFFFFF')
                txt_color = 'FFFFFF' if is_header else '1E293B'
                bold = is_header or (c_idx == 0)

                t_elm.append(f"""<w:tc>
                  <w:tcPr>
                    <w:tcW w:w="{width}" w:type="dxa"/>
                    <w:shd w:val="clear" w:color="auto" w:fill="{bg_color}"/>
                    <w:tcMar>
                      <w:top w:w="120" w:type="dxa"/>
                      <w:bottom w:w="120" w:type="dxa"/>
                      <w:left w:w="140" w:type="dxa"/>
                      <w:right w:w="140" w:type="dxa"/>
                    </w:tcMar>
                  </w:tcPr>
                  <w:p>
                    <w:pPr><w:spacing w:after="0"/><w:line w:line="240" w:lineRule="auto"/></w:pPr>
                    <w:r>
                      <w:rPr>
                        {'<w:b/>' if bold else ''}
                        <w:color w:val="{txt_color}"/>
                        <w:sz w:val="20"/>
                      </w:rPr>
                      <w:t xml:space="preserve">{html.escape(str(cell))}</w:t>
                    </w:r>
                  </w:p>
                </w:tc>""")
            t_elm.append('</w:tr>')
        t_elm.append('</w:tbl>')
        t_elm.append('<w:p><w:pPr><w:spacing w:after="160"/></w:pPr></w:p>')
        paragraphs.append(''.join(t_elm))

    # --- DOCUMENT GENERATION CONTENT ---

    # Header & Cover Title
    p("TRANSPORT MANAGEMENT SYSTEM (TMS)", bold=True, color="0D47A1", size=48, align="center", style="Title")
    p("Comprehensive System Architecture, Features, Database Schema & Operational Documentation", italic=True, color="475569", size=24, align="center", style="Subtitle")
    p("Generated: October 2026  |  Final Year BCA Project  |  Django 5.1 & Python 3.11", align="center", color="64748B", size=20)
    p()

    # 1. EXECUTIVE OVERVIEW
    p("1. Executive Project Overview", bold=True, style="Heading1")
    p("The Transport Management System (TMS) is a production-grade, enterprise-ready logistics and freight transport operations platform developed using Django (Python), MySQL, and modern Vanilla CSS glassmorphism UI principles. The system addresses end-to-end multi-city freight operations across India, connecting corporate consignors/customers, commercial fleet truck drivers, dispatch operations, and centralized platform administrators.")
    p("TMS manages the complete consignment lifecycle: initial customer registration, address and mobile verification, fleet equipment and license validation, automated driver allocation based on required truck types, duty-status-aware dispatching, live UUID package tracking, real-time driver delivery consoles with vertical stepper workflows, and automated email confirmations and status update notifications.")

    # High-level feature list
    bullet("Dual Role Portal", "Distinct operational workflows and dashboards tailored for Logistics Customers and Commercial Fleet Drivers.")
    bullet("Automated Driver Matching", "Real-time dispatch algorithm matching consignments to verified on-duty drivers based on required vehicle payload.")
    bullet("Dispatch Availability Locking", "Guarantees zero double-booking: once assigned, a driver is locked as busy ('Booked on Dispatch') and automatically released upon cargo delivery.")
    bullet("Public UUID Consignment Tracking", "Zero-login tracking engine featuring an interactive 5-step visual delivery progress timeline.")
    bullet("Indian Localization", "Pre-configured Indian states/UTs selector, +91 mobile verification, and standardized postal PIN code management.")
    bullet("Universal Floating Toast System", "High-performance fixed toast notification engine with 4-second auto-dismissal progress countdown and zero layout shift.")
    bullet("SMTP Email Communication Engine", "Automated email notifications on shipment creation and status updates sent to registered user inboxes.")

    p()

    # 2. TECHNOLOGY STACK
    p("2. Technology Stack & Environment Specifications", bold=True, style="Heading1")
    table([
        ["Layer / Component", "Technology / Framework", "Version / Details", "Purpose in System"],
        ["Backend Framework", "Django", "v5.1 / v5.2", "High-level Python web framework for models, views, and routing"],
        ["Core Language", "Python", "v3.11", "Runtime environment, object-oriented business logic"],
        ["Primary Database", "MySQL / SQLite", "MySQL 8.0 (localhost:3306)", "Relational data persistence with foreign keys and ACID transactions"],
        ["Frontend UI Architecture", "HTML5 + Vanilla CSS", "Modern Glassmorphism", "Dark-navy palette (#071224), translucent frosted glass, vibrant cyan accents"],
        ["CSS Framework & Icons", "Bootstrap & Bootstrap Icons", "v5.3 & v1.11.3", "Responsive grid layouts, utility classes, and iconography"],
        ["Email Protocol Backend", "SMTP (Google Mail)", "TLS / Port 587", "Automated booking confirmations and delivery status updates"],
        ["Authentication System", "Django Auth & Custom User", "AbstractUser Extension", "Role-based authorization (is_customer, is_driver, staff/admin)"],
        ["Signals & Event Hooks", "django.db.models.signals", "post_save, post_delete", "Automatic driver booking synchronization and status email dispatch"]
    ], [2200, 2200, 2200, 2800])

    p()

    # 3. DETAILED SYSTEM MODULES & FEATURES
    p("3. Detailed System Modules & Functionality", bold=True, style="Heading1")

    p("3.1 Role-Based Access Control & User Onboarding", bold=True, style="Heading2")
    p("The system implements a unified authentication and registration workflow with strict role partitioning:")
    bullet("Registration (sign_up)", "Users provide a unique username, valid email address, strong password, and select their operational role (Customer or Fleet Driver).")
    bullet("Email Collection & Validation", "Validates proper email syntax and performs database duplicate checks. Saves email directly to User.email and links to role profiles.")
    bullet("Duplicate Username Guard", "Performs case-insensitive username checks before hashing to prevent unhandled database IntegrityError crashes.")
    bullet("Login (login)", "Authenticates credentials against Django's PBKDF2 SHA-256 password hashes, establishing secure session cookies and directing users to role dashboards.")
    bullet("Session Routing & Navigation", "The navigation header (base.html) dynamically adjusts links: Customers see 'My Orders', Drivers see 'Assigned Deliveries' and 'Delivery History', and Guests see 'Log In' and 'Register'.")

    p("3.2 Customer Operations & Profile Management", bold=True, style="Heading2")
    p("Customers possess dedicated capabilities to manage their profile and book shipments:")
    bullet("Customer Profile (add_customer)", "Customers manage contact person name, +91 contact phone number, Indian State/UT dropdown, city name, street address, and PIN code.")
    bullet("Profile Completion Check", "Ensures delivery details are filled before dispatching shipments. Profiles are linked 1-to-1 with the authenticated user.")
    bullet("Customer Dashboard (home)", "Displays customer metrics, delivery address status, and direct booking action cards.")

    p("3.3 Fleet Management & Driver Operations", bold=True, style="Heading2")
    p("Commercial drivers possess an end-to-end fleet enrollment and active dispatch console:")
    bullet("Fleet Enrollment (add_driver)", "Drivers register Commercial Driving License (DL) number, contact phone, email, vehicle type, vehicle RC number, and license plate.")
    bullet("Fleet Verification (is_fleet_complete)", "A driver is only marked verified and eligible for load allocation when all vehicle and license specs are complete.")
    bullet("1-Click Duty Toggle (toggle_driver_duty)", "Drivers can switch between 'On Duty' (ready for dispatches) and 'Off Duty' (resting) with a single click button.")
    bullet("Active Deliveries Console (driver_deliveries)", "Lists all ongoing dispatches with pickup terminal, destination, cargo specs, customer contact, and route steppers.")
    bullet("Step-by-Step Dispatch Workflow", "Drivers progress shipments through 5 certified stages: Processing -> Shipped -> In Transit -> Out for Delivery -> Delivered.")
    bullet("Delivery History Archive (driver_history)", "Completed deliveries are automatically archived with timestamps, tracking codes, and metrics.")

    p("3.4 Smart Truck Selection & Automated Driver Allocation Engine", bold=True, style="Heading2")
    p("Consignment booking features a vehicle allocation engine:")
    bullet("6 Vehicle Categories", "Supports Small Truck (2.5T), Flatbed Truck (10T), Trailer Truck (25T), Tanker Truck (15kL), Container Truck (20T), and Mini Van (1T).")
    bullet("Live Driver Availability Counter", "Add Shipment dropdown displays real-time available driver counts for each truck category.")
    bullet("Interactive Route & Payload Card", "Selecting a truck instantly updates payload specs, carrier details, license plate preview, and green/red status indicators.")
    bullet("Zero Driver Available Lock", "If zero eligible drivers exist for a chosen truck, the submit button is locked and a floating warning alert is displayed.")
    bullet("Automated Driver Matching", "The system automatically matches the first eligible on-duty driver, eliminating manual search errors.")
    bullet("Automated Driver Booking", "Upon booking, the driver is immediately marked 'available = False' (Booked on Dispatch), preventing double-booking.")
    bullet("Auto-Release upon Delivery", "Once the driver marks the consignment 'Delivered', the driver is automatically unbooked and restored to available status.")

    p("3.5 Consignment Stepper Tracking Engine", bold=True, style="Heading2")
    p("Public-facing real-time tracking (track.html):")
    bullet("Zero-Login Tracking", "Any consignor or consignee can track cargo using their unique 36-character UUID tracking code.")
    bullet("5-Stage Vertical Stepper", "Visual progress bar showing: 1. Processing -> 2. Shipped -> 3. In Transit -> 4. Out for Delivery -> 5. Delivered.")
    bullet("Consignment Specs Card", "Displays origin/destination terminals, booking date, package description, quantity, and current status badge.")

    p("3.6 Universal Floating Toast Notification System", bold=True, style="Heading2")
    bullet("Zero Layout Shift (#tmsToastContainer)", "Fixed top-right viewport positioning lifts notifications out of DOM flow, eliminating shifting form elements.")
    bullet("4-Second Progress Bar", "Features an animated countdown progress bar that visualizes auto-dismissal over 4000ms.")
    bullet("Client & Server Integration", "Supports Python messages (messages.success/error) and JavaScript window.showTmsToast(msg, type).")

    p("3.7 Automated Email Notification Engine", bold=True, style="Heading2")
    bullet("SMTP TLS Integration", "Connects to Google SMTP with secure application credentials.")
    bullet("Booking Confirmation", "Dispatches an email immediately upon shipment creation containing the tracking ID and booking confirmation.")
    bullet("Live Dispatch Updates (signals.py)", "Post-save database signals detect status changes and email updates to the registered customer inbox.")

    p()

    # 4. DATABASE ARCHITECTURE & SCHEMA
    p("4. Database Architecture & Relational Schema", bold=True, style="Heading1")
    p("The system employs a relational schema with foreign key constraints, cascading rules, and UUID indexing:")

    p("Table 1: User (tms_application_user - Extends AbstractUser)", bold=True, style="Heading3")
    table([
        ["Field Name", "Data Type", "Constraints / Details", "Description"],
        ["id", "BigAuto (PK)", "Primary Key, Auto Increment", "Unique internal user identifier"],
        ["username", "VARCHAR(150)", "Unique, Required, Index", "Unique login username"],
        ["email", "VARCHAR(254)", "EmailField, Required", "User email address for notifications"],
        ["password", "VARCHAR(128)", "PBKDF2 SHA-256 Hashed", "Cryptographically hashed password"],
        ["is_customer", "BOOLEAN", "Default: False", "Flags user as having customer privileges"],
        ["is_driver", "BOOLEAN", "Default: False", "Flags user as commercial fleet driver"],
        ["date_joined", "DATETIME", "Default: timezone.now", "Account creation timestamp"]
    ], [1800, 1800, 2400, 3400])

    p("Table 2: NewCustomer (Customer Profile)", bold=True, style="Heading3")
    table([
        ["Field Name", "Data Type", "Constraints / Details", "Description"],
        ["id", "BigAuto (PK)", "Primary Key, Auto Increment", "Unique customer record identifier"],
        ["user_id", "ForeignKey(User)", "CASCADE, Nullable", "One-to-one pointer to auth User account"],
        ["customer_name", "VARCHAR(100)", "Required", "Full name of customer / company contact"],
        ["phone_number", "VARCHAR(15)", "Required", "Contact mobile number (+91 format)"],
        ["email", "VARCHAR(254)", "EmailField, Required", "Customer correspondence email"],
        ["address", "VARCHAR(255)", "Required", "Building, street, flat, and landmark"],
        ["city", "VARCHAR(100)", "Nullable, Required in UI", "Delivery city / town name"],
        ["state", "VARCHAR(100)", "Nullable, 36 Indian States/UTs", "Indian State or Union Territory"],
        ["pincode", "VARCHAR(10)", "Nullable, Postal PIN", "6-digit postal PIN code"]
    ], [1800, 1800, 2400, 3400])

    p("Table 3: NewDriver (Fleet Driver & Equipment Profile)", bold=True, style="Heading3")
    table([
        ["Field Name", "Data Type", "Constraints / Details", "Description"],
        ["id", "BigAuto (PK)", "Primary Key, Auto Increment", "Unique driver record identifier"],
        ["user_id", "ForeignKey(User)", "CASCADE, Nullable", "Pointer to authenticated driver User account"],
        ["driver_name", "VARCHAR(100)", "Required", "Official full name of fleet driver"],
        ["license_number", "VARCHAR(20)", "Required", "Commercial Heavy/Light Vehicle Driving License"],
        ["phone_number", "VARCHAR(15)", "Required", "Driver mobile phone number"],
        ["email", "VARCHAR(254)", "EmailField, Required", "Driver notification email address"],
        ["vehicle_type", "VARCHAR(3)", "Choices: ST, FT, TrR, TkT, CT, MV", "Assigned fleet truck equipment class"],
        ["vehicle_registration_number", "VARCHAR(50)", "Required", "Official Government Vehicle RC Number"],
        ["vehicle_number_plate", "VARCHAR(20)", "Required", "License plate stamped on truck"],
        ["available", "BOOLEAN", "Choices: True (Yes), False (No)", "Real-time dispatch duty and booking availability"]
    ], [2200, 1800, 2200, 3200])

    p("Table 4: NewShipment (Consignment Cargo Record)", bold=True, style="Heading3")
    table([
        ["Field Name", "Data Type", "Constraints / Details", "Description"],
        ["id", "BigAuto (PK)", "Primary Key, Auto Increment", "Unique internal consignment ID"],
        ["tracking_id", "UUIDField", "default=uuid4, unique=True", "36-char public consignment tracking code"],
        ["user_id", "ForeignKey(User)", "CASCADE, Nullable", "Customer user account that booked shipment"],
        ["customer_id", "ForeignKey(NewCustomer)", "CASCADE, Nullable", "Associated customer delivery profile"],
        ["driver_id", "ForeignKey(NewDriver)", "SET_NULL, Nullable", "Assigned on-duty commercial fleet driver"],
        ["truck_type", "VARCHAR(10)", "Choices: ST, FT, TrR, TkT, CT, MV", "Truck vehicle class required for cargo"],
        ["order_date", "DATE", "Nullable", "Date consignment booking was initiated"],
        ["shipment_date", "DATE", "Nullable", "Date cargo was dispatched or delivered"],
        ["package_description", "TEXT", "Nullable", "Description of goods, cargo nature, handling"],
        ["quantity", "INTEGER", "Nullable", "Package count, cartons, or total consignment units"],
        ["from_destination", "VARCHAR(255)", "Choices: MI (Mumbai), DL (Delhi), AMD (Ahmedabad)", "Origin logistics freight terminal"],
        ["to_destination", "VARCHAR(255)", "Choices: MI, DL, AMD", "Destination freight terminal"],
        ["status", "VARCHAR(20)", "processing, shipped, in_transit, out_for_delivery, delivered", "Current live delivery lifecycle stage"]
    ], [2000, 1800, 2400, 3200])

    p()

    # 5. URL ROUTING & API ENDPOINTS
    p("5. System URL Routing & Endpoint Map", bold=True, style="Heading1")
    table([
        ["URL Path", "Route Name", "HTTP Methods", "Access Level", "Purpose & View Action"],
        ["/", "index", "GET", "Public (Guest)", "Landing splash page with hero CTA and portal entry"],
        ["/home/", "home", "GET", "Role-Aware", "Central operations dashboard for Customer, Driver, or Guest"],
        ["/about/", "about", "GET", "Public", "Company background, fleet network, and warehouse locations"],
        ["/services/", "services", "GET", "Public", "Freight services, supply chain solutions, express transport"],
        ["/pricing/", "pricing", "GET", "Public", "Freight pricing tiers, container rates, and custom quotes"],
        ["/contact/", "contact", "GET, POST", "Public", "Contact support inquiry form with email relay"],
        ["/login/", "login", "GET, POST", "Unauthenticated", "User authentication with role redirect"],
        ["/sign_up/", "sign_up", "GET, POST", "Unauthenticated", "Account registration with email and role selection"],
        ["/logout/", "logout", "POST", "Authenticated", "Clears session and redirects to index"],
        ["/track/", "track", "GET, POST", "Public", "Consignment tracking with 5-stage stepper"],
        ["/orders/", "order_history", "GET", "Customer Only", "Customer order history table with copy tracking code"],
        ["/add_shipment/", "add_shipment", "GET, POST", "Customer Only", "Freight booking with live truck and driver allocation"],
        ["/add_customer/", "add_customer", "GET, POST", "Customer Only", "Customer profile, delivery address, and PIN setup"],
        ["/add_driver/", "add_driver", "GET, POST", "Driver Only", "Driver fleet enrollment and equipment verification"],
        ["/driver/deliveries/", "driver_deliveries", "GET", "Driver Only", "Active dispatch management and route status advancement"],
        ["/driver/deliveries/update/<id>/", "update_delivery_status", "POST", "Driver Only", "Advances shipment status and auto-releases driver"],
        ["/driver/duty/toggle/", "toggle_driver_duty", "GET, POST", "Driver Only", "1-click toggle between On Duty and Off Duty"],
        ["/driver/history/", "driver_history", "GET", "Driver Only", "Driver archived delivered consignments with metrics"],
        ["/admin/", "django_admin", "GET, POST", "Staff / Superuser", "Django administrative CRUD panel"]
    ], [2200, 1800, 1400, 1600, 2400])

    p()

    # 6. STEP-BY-STEP USER WORKFLOWS
    p("6. Operational Workflows & User Journeys", bold=True, style="Heading1")

    p("Workflow 1: Customer Consignment Booking & Delivery", bold=True, style="Heading2")
    bullet("Step 1 (Sign Up)", "User creates an account at /sign_up/, inputs their email, selects role 'Customer', and logs in.")
    bullet("Step 2 (Profile Setup)", "Navigates to /add_customer/ and saves delivery address, city, Indian state, PIN, and +91 phone.")
    bullet("Step 3 (Shipment Creation)", "Visits /add_shipment/, chooses pickup terminal (e.g. Mumbai MI) and destination (e.g. Delhi DL).")
    bullet("Step 4 (Truck Selection)", "Selects a truck type (e.g. Small Truck). The live card previews matched driver name, license plate, and payload capacity.")
    bullet("Step 5 (Booking Confirmation)", "Clicks 'Register & Dispatch Shipment'. Driver is immediately booked (available = False). System dispatches an email with tracking UUID.")
    bullet("Step 6 (Order Tracking)", "Customer views order in /orders/ or tracks live shipment status at /track/?tracking_id=<uuid>.")

    p("Workflow 2: Driver Dispatch Management & Delivery Execution", bold=True, style="Heading2")
    bullet("Step 1 (Driver Sign Up)", "Driver registers at /sign_up/, enters email, selects 'Fleet Driver', and logs in.")
    bullet("Step 2 (Fleet Registration)", "Navigates to /add_driver/, fills in license DL, phone, truck type, RC registration number, and plate number. Sets Duty Status to 'Available'.")
    bullet("Step 3 (Consignment Assignment)", "When a customer books that vehicle type, the driver is automatically assigned and locked as 'Booked on Dispatch'.")
    bullet("Step 4 (Delivery Operations)", "Driver visits /driver/deliveries/ and advances status: Processing -> Shipped -> In Transit -> Out for Delivery -> Delivered.")
    bullet("Step 5 (Automatic Unbooking)", "Upon marking 'Delivered', the system updates delivery date, releases driver back to 'Available for Loads' (available = True), and archives the record to /driver/history/.")

    p()

    # 7. SECURITY & ERROR RESILIENCE
    p("7. Security Architecture & Error Resilience", bold=True, style="Heading1")
    bullet("CSRF Protection", "Every form enforces Django {% csrf_token %} against Cross-Site Request Forgery.")
    bullet("Password Cryptography", "PBKDF2 SHA-256 algorithm with cryptographic salting prevents credential compromise.")
    bullet("Integrity Error Prevention", "Case-insensitive username and email lookups prevent duplicate key integrity crashes.")
    bullet("Role Authorization Guards", "View decorators and session attribute checks prevent customers from accessing driver consoles and vice versa.")
    bullet("Zero Double-Booking Guarantee", "Simultaneous active consignment checks prevent a single driver from being assigned to multiple concurrent shipments.")
    bullet("Input Sanitization", "Origin and destination terminal equality checks prevent invalid identical-route bookings.")

    p()

    # 8. FUTURE ROADMAP
    p("8. Future Roadmap & Enhancement Scope", bold=True, style="Heading1")
    bullet("Live GPS Telematics", "Integrate Leaflet.js / Google Maps API with real-time GPS coordinates from driver smartphones.")
    bullet("Digital Invoicing & Payments", "Razorpay / Stripe integration for instant freight bill generation and online customer payments.")
    bullet("Digital Proof of Delivery (e-POD)", "Consignee digital signature capture and delivery photo upload upon cargo receipt.")
    bullet("Automated SMS Gateway", "Twilio / Fast2SMS integration for live SMS dispatch alerts to customer phone numbers.")

    # Write out to ZIP DOCX file
    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
  </w:body>
</w:document>"""

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/_rels/document.xml.rels', doc_rels)
        z.writestr('word/styles.xml', styles)
        z.writestr('word/document.xml', doc_xml)

    print(f"DOCX_CREATED_AT: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TMS_Project_Documentation.docx")
    create_docx(out_file)
