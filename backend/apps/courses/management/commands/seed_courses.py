from django.core.management.base import BaseCommand
from apps.courses.models import CourseCategory, Course


CATEGORIES = [
    {"slug": "power-systems",       "name": "Power Systems & High Voltage",          "moodle_id": 1001},
    {"slug": "electrical-installation", "name": "Electrical Installation",           "moodle_id": 1002},
    {"slug": "mechanical-industrial",   "name": "Mechanical & Industrial Engineering","moodle_id": 1003},
    {"slug": "civil-construction",      "name": "Civil & Construction Engineering",   "moodle_id": 1004},
    {"slug": "renewable-energy",        "name": "Renewable Energy & Sustainability",  "moodle_id": 1005},
    {"slug": "management-leadership",   "name": "Management, Finance & Leadership",   "moodle_id": 1006},
    {"slug": "safety-compliance",       "name": "Health, Safety & HR Compliance",     "moodle_id": 1007},
]

# (shortname, fullname, duration_days, price_usd, level, category_slug, summary)
COURSES = [
    # ── POWER SYSTEMS & HIGH VOLTAGE ─────────────────────────────────────
    (
        "33KV-SWITCH", "33KV Switching Fundamentals",
        5, 325, "INTERMEDIATE", "power-systems",
        "Covers the principles and safe operational procedures for 33KV switching "
        "in ZESA substations and distribution networks. Includes switching schedules, "
        "isolation, earthing, and permit-to-work systems.",
    ),
    (
        "132KV-SWITCH", "132KV Switching Fundamentals",
        15, 636, "ADVANCED", "power-systems",
        "Advanced high-voltage switching operations at 132KV level. Covers system "
        "topology, switching sequences, fault clearance, and safety protocols for "
        "transmission substations. Three-week intensive programme.",
    ),
    (
        "PSP1", "Power Systems Protection I",
        5, 325, "INTERMEDIATE", "power-systems",
        "Fundamentals of power system protection including relay types, settings, "
        "coordination principles, overcurrent and earth fault protection, and "
        "testing procedures.",
    ),
    (
        "PSP2", "Power Systems Protection II",
        5, 325, "ADVANCED", "power-systems",
        "Advanced protection schemes including differential protection, distance "
        "relays, busbar protection, and modern numerical relay configuration. "
        "Prerequisite: Power Systems Protection I.",
    ),
    (
        "SUB-MAINT", "Substation & Transformer Maintenance",
        5, 325, "INTERMEDIATE", "power-systems",
        "Maintenance practices for power transformers, switchgear, and substation "
        "equipment. Covers oil testing, insulation resistance, dissolved gas "
        "analysis, and planned maintenance scheduling.",
    ),
    (
        "VFD-SS", "Variable Frequency Drives and Soft Starters",
        5, 325, "INTERMEDIATE", "power-systems",
        "Installation, commissioning, programming, and troubleshooting of VFDs "
        "and soft starters used in pump stations, fans, and industrial motors "
        "across ZESA facilities.",
    ),
    (
        "LL-MAINT", "Live Line Maintenance",
        10, 481, "ADVANCED", "power-systems",
        "Techniques and safety requirements for working on energised overhead "
        "lines. Covers bare-hand and hot-stick methods, personal protective "
        "equipment, and live-line tools. Two-week hands-on programme.",
    ),
    (
        "DIST-PLAN", "Distribution Network Planning",
        3, 270, "INTERMEDIATE", "power-systems",
        "Load flow analysis, network design, capacity planning, and loss "
        "reduction strategies for 33KV and 11KV distribution networks.",
    ),
    (
        "PS-COMM", "Power Systems Communication Protocols",
        5, 325, "INTERMEDIATE", "power-systems",
        "DNP3, IEC 61850, MODBUS, and SCADA communication protocols used in "
        "modern power system control and monitoring. Practical configuration "
        "exercises included.",
    ),
    (
        "METERING", "Metering",
        5, 325, "BEGINNER", "power-systems",
        "Energy metering principles, meter types, tariff structures, meter "
        "testing, and anti-tamper measures for residential, commercial, and "
        "industrial installations.",
    ),
    (
        "MINIGRID", "Mini Grid Installation, Operations and Maintenance",
        5, 325, "INTERMEDIATE", "power-systems",
        "Design, installation, commissioning, and O&M of rural mini-grids "
        "including hybrid solar-diesel systems, battery storage, and load "
        "management controllers.",
    ),
    (
        "DIG-PWR", "Digital Transformation in Power Sector",
        5, 325, "ALL_LEVELS", "power-systems",
        "Overview of smart grid technologies, IoT in utilities, digital "
        "SCADA, AMI, predictive analytics, and the strategic roadmap for "
        "digital transformation in power utilities.",
    ),

    # ── ELECTRICAL INSTALLATION ──────────────────────────────────────────
    (
        "LSMAN1", "Basic Linesman 1 Course",
        10, 481, "BEGINNER", "electrical-installation",
        "Foundation course for electrical linesmen covering basic electrical "
        "theory, pole climbing, overhead line construction, conductor stringing, "
        "and safety on overhead networks. Two-week practical programme.",
    ),
    (
        "LSMAN2", "Basic Linesman 2 Course",
        10, 481, "INTERMEDIATE", "electrical-installation",
        "Continuation of Basic Linesman 1. Covers underground cable systems, "
        "jointing, transformer connections, service connections, and LV "
        "network fault-finding. Prerequisite: Basic Linesman 1.",
    ),
    (
        "DOM-INST", "Domestic Installation",
        10, 481, "BEGINNER", "electrical-installation",
        "Practical installation of domestic wiring systems including single "
        "and three-phase circuits, distribution boards, earthing systems, "
        "and compliance with Zimbabwe wiring regulations. Two-week course.",
    ),
    (
        "CABLE-XPLE", "Cable Jointing and Termination XLPE",
        5, 325, "INTERMEDIATE", "electrical-installation",
        "Hands-on training in jointing and terminating XLPE insulated cables "
        "for LV and MV systems. Covers preparation, stress control, insulation "
        "restoration, and pressure testing.",
    ),

    # ── MECHANICAL & INDUSTRIAL ──────────────────────────────────────────
    (
        "ARC-WELD", "Arc and Gas Welding",
        10, 481, "BEGINNER", "mechanical-industrial",
        "Fundamentals of manual metal arc (MMA) and oxy-acetylene welding "
        "including joint preparation, welding positions, defect identification, "
        "and workshop safety. Two-week practical course.",
    ),
    (
        "TIG-MIG", "Tungsten & Metal Inert Gas Welding (TIG & MIG)",
        10, 481, "INTERMEDIATE", "mechanical-industrial",
        "Advanced welding using TIG (GTAW) and MIG (GMAW) processes on steel, "
        "stainless steel, and aluminium. Covers shielding gases, filler "
        "selection, and weld quality inspection. Prerequisite: Arc welding.",
    ),
    (
        "HYDRAULICS", "Applied Industrial Hydraulics",
        5, 325, "INTERMEDIATE", "mechanical-industrial",
        "Hydraulic circuit design, components (pumps, valves, actuators, "
        "accumulators), system commissioning, troubleshooting, and maintenance "
        "for industrial hydraulic systems.",
    ),
    (
        "PUMP-TECH", "Pump Technology",
        5, 325, "INTERMEDIATE", "mechanical-industrial",
        "Types of pumps, performance curves, cavitation, impeller selection, "
        "alignment, mechanical seals, and maintenance of centrifugal and "
        "positive displacement pumps in water and power plant applications.",
    ),
    (
        "VALVE-TECH", "Valve Technology",
        5, 325, "INTERMEDIATE", "mechanical-industrial",
        "Gate, globe, butterfly, ball, and pressure relief valves — selection, "
        "installation, operation, and maintenance for industrial pipework "
        "and power station applications.",
    ),
    (
        "VIB-ANLYS", "Machinery Vibration Monitoring and Analysis",
        5, 325, "INTERMEDIATE", "mechanical-industrial",
        "Vibration theory, measurement techniques, data collection, spectrum "
        "analysis, and fault diagnosis for rotating machinery including "
        "motors, pumps, fans, and compressors.",
    ),
    (
        "RIGGING", "Rigging and Safe Lifting Techniques",
        5, 325, "ALL_LEVELS", "mechanical-industrial",
        "Safe rigging practices, sling types and capacities, crane signals, "
        "load calculations, inspection of lifting tackle, and legal "
        "requirements for lifting operations.",
    ),

    # ── CIVIL & CONSTRUCTION ─────────────────────────────────────────────
    (
        "CONCRETE", "Concrete Technology",
        5, 325, "INTERMEDIATE", "civil-construction",
        "Mix design, water-cement ratio, admixtures, curing, testing methods "
        "(slump, cube strength), and quality control for concrete used in "
        "substation bases, poles, and civil structures.",
    ),
    (
        "CIVIL-CONT", "Civil Engineering Contracts",
        5, 325, "INTERMEDIATE", "civil-construction",
        "FIDIC contract forms, NEC contracts, procurement procedures, contract "
        "administration, claims, disputes, and contractor management for civil "
        "engineering and construction projects.",
    ),
    (
        "CIVIL-NCE", "Civil Engineering for Non-Civil Engineers",
        10, 481, "BEGINNER", "civil-construction",
        "Introduction to soil mechanics, foundations, concrete, structural "
        "elements, and site supervision for electrical and mechanical engineers "
        "who work alongside civil teams. Two-week course.",
    ),
    (
        "CIVIL-TX", "Civil Works in Transmission Line & Substation Construction",
        5, 325, "INTERMEDIATE", "civil-construction",
        "Foundation design and construction for lattice towers and poles, "
        "substation civil works, cable trenching, road access, and site "
        "drainage for power infrastructure projects.",
    ),

    # ── RENEWABLE ENERGY & SUSTAINABILITY ───────────────────────────────
    (
        "SOLAR-PV", "Solar PV Systems Design, Installation & Maintenance",
        5, 325, "INTERMEDIATE", "renewable-energy",
        "Site assessment, system sizing, component selection (panels, inverters, "
        "batteries, charge controllers), installation standards, commissioning, "
        "fault-finding, and O&M for solar PV systems.",
    ),
    (
        "ENERGY-EFF", "Energy Efficiency in Buildings",
        5, 325, "ALL_LEVELS", "renewable-energy",
        "Building energy performance assessment, HVAC efficiency, lighting "
        "upgrades, insulation, energy monitoring, and practical measures to "
        "reduce consumption in commercial and residential buildings.",
    ),
    (
        "LOAD-FCST", "Load Forecasting & Energy Efficiency in Buildings",
        5, 325, "INTERMEDIATE", "renewable-energy",
        "Demand-side forecasting methodologies, load profiling, energy "
        "modelling tools, and integrated energy efficiency strategies for "
        "building portfolios and distribution planning.",
    ),
    (
        "EE-AUDIT", "Energy Efficiency & Audit",
        5, 325, "INTERMEDIATE", "renewable-energy",
        "Conducting energy audits to ISO 50002 guidelines, data gathering, "
        "baseline analysis, identifying savings opportunities, investment "
        "payback calculations, and audit reporting.",
    ),
    (
        "ISO-50001", "ISO 50001 Energy Management",
        5, 325, "INTERMEDIATE", "renewable-energy",
        "Requirements and implementation of ISO 50001 Energy Management "
        "Systems including energy policy, EnMS planning, energy review, "
        "targets, action plans, and internal audit.",
    ),
    (
        "SUST-ENG", "Sustainable Engineering Practices",
        5, 325, "ALL_LEVELS", "renewable-energy",
        "Principles of sustainable design, life-cycle assessment, green "
        "procurement, carbon footprint reduction, and environmental impact "
        "management for engineering professionals.",
    ),

    # ── MANAGEMENT, FINANCE & LEADERSHIP ────────────────────────────────
    (
        "CORP-GOV-MGR", "Corporate Governance Legislation Appreciation for Managers",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Zimbabwe Companies Act, Public Entities Corporate Governance Act, "
        "board responsibilities, risk oversight, compliance frameworks, "
        "and governance best practice for middle and senior managers.",
    ),
    (
        "CORP-GOV-ETH", "Corporate Governance and Work Ethics",
        2, 240, "ALL_LEVELS", "management-leadership",
        "Principles of ethical conduct, conflict of interest, anti-corruption, "
        "professional accountability, and the code of conduct applicable to "
        "all ZESA employees.",
    ),
    (
        "LABOUR-LAW", "Labour Law Appreciation",
        5, 325, "ALL_LEVELS", "management-leadership",
        "Zimbabwe Labour Act provisions, employment contracts, disciplinary "
        "procedures, retrenchment, collective bargaining, and labour dispute "
        "resolution for line managers and HR practitioners.",
    ),
    (
        "VFL", "Visual Felt Leadership",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Leadership through visible presence, safety leadership walks, "
        "coaching conversations, and building a high-performance culture "
        "through frontline engagement.",
    ),
    (
        "PRE-RET", "Pre-Retirement Training",
        5, 325, "ALL_LEVELS", "management-leadership",
        "Financial planning, health and wellness, post-retirement opportunities, "
        "legal matters, and psychological preparation for employees approaching "
        "retirement.",
    ),
    (
        "ISO-31000", "ISO 31000 Risk Management Appreciation",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Risk management principles and guidelines per ISO 31000:2018, risk "
        "identification, assessment, treatment, monitoring, and integration "
        "into organisational governance.",
    ),
    (
        "IRBM", "Integrated Results-Based Management (IRBM) Training",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Results-based planning, performance contracts, performance measurement "
        "frameworks, reporting, and accountability systems aligned to Zimbabwe's "
        "public sector IRBM requirements.",
    ),
    (
        "MIN-WRITE", "Minutes Writing Training",
        5, 325, "BEGINNER", "management-leadership",
        "Structure and format of minutes, action items, resolutions, accuracy "
        "and objectivity in recording, and distribution of minutes for "
        "formal and informal meetings.",
    ),
    (
        "TRANSPORT", "Transport and Logistics Management",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Fleet management, route planning, vehicle maintenance scheduling, "
        "fuel management, driver safety, logistics costs, and compliance "
        "with transport regulations.",
    ),
    (
        "INVENTORY", "Inventory Management",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Stock control systems, reorder points, ABC analysis, cycle counting, "
        "warehouse layout, materials handling, and integration with SAP "
        "inventory modules.",
    ),
    (
        "PROJ-CM", "Project Contract Management",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Contract strategy, tendering, evaluation, award, contract monitoring, "
        "variation orders, claims management, and close-out for capital "
        "and service contracts.",
    ),
    (
        "ENG-PM", "Engineering Project Management",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Project lifecycle management for engineering projects including scope "
        "definition, scheduling (CPM/PERT), resource planning, cost control, "
        "risk management, and project reporting.",
    ),
    (
        "PRINCE2", "PRINCE 2 Foundation",
        5, 325, "INTERMEDIATE", "management-leadership",
        "PRINCE2 methodology covering the seven principles, themes, and "
        "processes for structured project management. Aligned to the "
        "PRINCE2 Foundation certification syllabus.",
    ),
    (
        "FIN-REP", "Financial Reporting",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Preparation and interpretation of financial statements (income "
        "statement, balance sheet, cash flow), IFRS principles, ratio "
        "analysis, and financial reporting for non-finance managers.",
    ),
    (
        "VAT-TRAIN", "VAT Training",
        5, 325, "ALL_LEVELS", "management-leadership",
        "Zimbabwe VAT Act requirements, registration, input and output tax, "
        "VAT returns, record-keeping, and common compliance errors for "
        "finance and procurement staff.",
    ),
    (
        "INT-CTRL", "Internal Controls: Prevention and Detection of Fraud",
        5, 325, "INTERMEDIATE", "management-leadership",
        "Fraud risk assessment, internal control frameworks (COSO), red "
        "flags and detection techniques, whistleblower mechanisms, and "
        "forensic investigation basics.",
    ),
    (
        "CLIENT-CARE", "Client Care",
        2, 240, "ALL_LEVELS", "management-leadership",
        "Customer service principles, handling complaints, communication "
        "skills, telephone etiquette, and service recovery for "
        "customer-facing and frontline staff.",
    ),

    # ── HEALTH, SAFETY & HR COMPLIANCE ──────────────────────────────────
    (
        "OHS-PS", "Occupational Health and Safety in Power Systems",
        5, 325, "ALL_LEVELS", "safety-compliance",
        "Legal framework (NSSA Act, SI 31), hazard identification, risk "
        "assessment, electrical safety, permit-to-work, PPE, incident "
        "investigation, and safety management systems for power utilities.",
    ),
    (
        "WORKERS-COM", "Workers Committee Course",
        3, 270, "ALL_LEVELS", "safety-compliance",
        "Role and functions of workers committees under the Zimbabwe Labour "
        "Act, collective bargaining, representing employee interests, "
        "and conducting effective meetings.",
    ),
    (
        "EMP-REL", "Employee Relations and Code of Conduct",
        5, 325, "ALL_LEVELS", "safety-compliance",
        "Managing the employment relationship, disciplinary procedures, "
        "grievance handling, misconduct categories, and applying the "
        "ZESA code of conduct consistently and fairly.",
    ),
    (
        "GRIEVANCE", "Grievance Handling Procedures",
        5, 325, "ALL_LEVELS", "safety-compliance",
        "Step-by-step grievance procedures, investigation techniques, "
        "resolution approaches, documentation, and preventing grievances "
        "from escalating to Labour Court.",
    ),
    (
        "ESG", "Environmental, Social and Governance (ESG)",
        5, 325, "ALL_LEVELS", "safety-compliance",
        "ESG frameworks, environmental impact management, social licence to "
        "operate, governance disclosure, stakeholder engagement, and "
        "sustainability reporting for ZESA operations.",
    ),
    (
        "NSSA", "NSSA Processes Appreciation",
        5, 325, "ALL_LEVELS", "safety-compliance",
        "NSSA registration, contribution rates, workplace injury claims, "
        "compensation processes, workplace hazard reporting, and NSSA "
        "inspection requirements for employers.",
    ),
    (
        "RPA-DRONE", "Remotely Piloted Aircraft (RPA) Training",
        5, 1260, "ADVANCED", "safety-compliance",
        "CAA Zimbabwe-approved training for operating remotely piloted "
        "aircraft (drones) for powerline inspection, survey, and aerial "
        "photography. Covers regulations, flight operations, emergency "
        "procedures, and practical flying assessment.",
    ),
]


class Command(BaseCommand):
    help = "Wipe demo courses/categories and seed with real ZNTC training data"

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing courses and categories...")
        Course.objects.all().delete()
        CourseCategory.objects.all().delete()
        self.stdout.write(self.style.WARNING("  Deleted all existing records."))

        cat_map = {}
        for cat_data in CATEGORIES:
            cat = CourseCategory.objects.create(
                name=cat_data["name"],
                moodle_id=cat_data["moodle_id"],
            )
            cat_map[cat_data["slug"]] = cat
            self.stdout.write(f"  Category: {cat.name}")

        self.stdout.write(f"\nCreated {len(cat_map)} categories.")

        created = 0
        for idx, course_data in enumerate(COURSES, start=1):
            shortname, fullname, duration_days, price, level, cat_slug, summary = course_data
            Course.objects.create(
                shortname=shortname,
                fullname=fullname,
                summary=summary,
                duration_days=duration_days,
                price=price,
                level=level,
                category=cat_map[cat_slug],
                is_active=True,
                requires_approval=True,
                max_capacity=20,
                enrolled_count=0,
                moodle_course_id=2000 + idx,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created} courses across {len(cat_map)} categories."
        ))
