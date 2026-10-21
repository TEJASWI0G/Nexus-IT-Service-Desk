import streamlit as st
import uuid
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from datetime import timezone
import plotly.express as px


def format_ist(timestamp):
    if not timestamp:
        return ""

    timestamp_utc = datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )

    from datetime import timezone
    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

    timestamp_ist = timestamp_utc.astimezone(
        timezone(timedelta(hours=5, minutes=30))
    )

    return timestamp_ist.strftime("%Y-%m-%d %H:%M")



def calculate_sla(priority, created_at):
    from datetime import timezone

    sla_hours = {
        "High": 4,
        "Medium": 8,
        "Low": 24,
    }

    if not created_at:
        return None

    created_time = datetime.strptime(
        created_at,
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    deadline = created_time + timedelta(
        hours=sla_hours.get(priority, 24)
    )

    ist = timezone(timedelta(hours=5, minutes=30))

    return deadline.astimezone(ist)



def check_sla_status(priority, created_at, status):
    if status == "Resolved":
        return "Resolved"

    deadline = calculate_sla(priority, created_at)

    if deadline is None:
        return "Unknown"


    current_time = datetime.now(
        timezone(timedelta(hours=5, minutes=30))
    )

    if current_time > deadline:
        return "SLA Breached"

    return "Within SLA"



st.set_page_config(
    page_title="Nexus | IT Service Desk",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)




st.markdown(
    """

    <style>
    /* CYBERPUNK NEXUS — GLOBAL THEME */
    :root {
        --bg-main: #070B14;
        --bg-panel: #0D1424;
        --bg-card: #101C30;
        --neon-cyan: #00F5FF;
        --neon-blue: #3980FF;
        --neon-purple: #A855F7;
        --text-main: #E6F7FF;
        --text-muted: #8BA3BD;
        --border-neon: rgba(0, 245, 255, 0.24);
    }

    /* Application background */
    .stApp {
        background:
            radial-gradient(
                circle at 85% 5%,
                rgba(0, 100, 255, 0.10),
                transparent 30%
            ),
            linear-gradient(135deg, #070B14, #090F1E 60%, #070B14);
        color: var(--text-main);
    }

    /* Remove excess top whitespace */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    [data-testid="stAppViewBlockContainer"] {
        padding-top: 0.5rem !important;
    }

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1600px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1221, #080D18);
        border-right: 1px solid var(--border-neon);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--neon-cyan) !important;
        letter-spacing: 2px;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--border-neon);
    }

    /* Headings */

    h1, h2, h3 {
        color: var(--text-main) !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    h1 {
        font-size: 1.8rem !important;
        text-shadow: 0 0 18px rgba(0, 245, 255, 0.18);
    }

    h2 {
        font-size: 1.5rem !important;
    }

    h3 {
        font-size: 1.2rem !important;
    }

    /* General text */
    p, label, [data-testid="stCaptionContainer"] {
        color: var(--text-muted);
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #111E33, #0B1425);
        border: 1px solid var(--border-neon);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 14px rgba(0, 245, 255, 0.035);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--neon-cyan);
        box-shadow: 0 0 16px rgba(0, 245, 255, 0.12);
    }

    [data-testid="stMetricLabel"] {
        color: #9CB5CF !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--neon-cyan) !important;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(100deg, #075985, #155EEF);
        color: #FFFFFF !important;
        border: 1px solid rgba(0, 245, 255, 0.55);
        border-radius: 8px;
        padding: 0.55rem 1rem;
        font-weight: 650;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(100deg, #0891B2, #2563EB);
        border-color: var(--neon-cyan);
        box-shadow: 0 0 16px rgba(0, 245, 255, 0.22);
        transform: translateY(-1px);
    }

    /* Text fields */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #0B1425 !important;
        color: var(--text-main) !important;
        border: 1px solid #263C58 !important;
        border-radius: 8px;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 0 1px var(--neon-cyan);
    }

    /* Dropdowns */
    [data-baseweb="select"] > div {
        background-color: #0B1425;
        border-color: #263C58;
        color: var(--text-main);
    }

    /* Radio navigation */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #C7D8EC;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-neon);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Dividers */
    hr {
        border-color: rgba(0, 245, 255, 0.16);
    }

    /* Notifications */
    [data-testid="stAlert"] {
        border-radius: 8px;
    }

    /* Charts */
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"] {
        background: rgba(13, 20, 36, 0.55);
        border: 1px solid rgba(0, 245, 255, 0.12);
        border-radius: 12px;
        padding: 10px;
    }

    /* Bluish-purple analytics charts */
    [data-testid="stVegaLiteChart"] svg rect[fill],
    [data-testid="stArrowVegaLiteChart"] svg rect[fill] {
        fill: #7966FF !important;
    }

    
    /* Vibrant white text on all buttons */
    .stButton > button,
    .stButton > button p,
    .stButton > button span,
    .stDownloadButton > button,
    .stDownloadButton > button p,
    .stDownloadButton > button span,
    button[kind] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        text-shadow: 0 0 6px rgba(255, 255, 255, 0.18);
    }

    /* Keep button text white when hovering */
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind]:hover {
        color: #FFFFFF !important;
    }


    /* ===== NEXUS ANIMATED TOP NAVIGATION ===== */

    div[role="radiogroup"]:has(input[type="radio"]) {
        gap: 12px !important;
    }

    div[role="radiogroup"] label {
        position: relative !important;
        isolation: isolate !important;
        overflow: visible !important;
        border: 1px solid rgba(168, 85, 247, 0.20) !important;
        background: rgba(20, 16, 40, 0.55) !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        transition:
            transform 300ms ease,
            background 350ms ease,
            border-color 350ms ease,
            box-shadow 350ms ease !important;
    }

    /* Expanding purple-pink glow */
    div[role="radiogroup"] label::before {
        content: "" !important;
        position: absolute !important;
        inset: -3px !important;
        z-index: -1 !important;
        border-radius: 14px !important;
        background: linear-gradient(110deg, #8B5CF6, #EC4899) !important;
        opacity: 0 !important;
        filter: blur(12px) !important;
        transform: scale(0.85) !important;
        transition:
            opacity 350ms ease,
            transform 350ms ease !important;
        pointer-events: none !important;
    }

    /* Bright white navigation text */
    div[role="radiogroup"] label p,
    div[role="radiogroup"] label span {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        transition: color 300ms ease, text-shadow 300ms ease !important;
    }

    /* Hover animation */


    div[role="radiogroup"] label {
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }   

    div[role="radiogroup"] label:hover {
        border-color: rgba(192, 132, 252, 0.65) !important;
        background: rgba(139, 92, 246, 0.10) !important;
        box-shadow:
            0 0 10px rgba(139, 92, 246, 0.12),
            0 0 14px rgba(236, 72, 153, 0.08) !important;
    }



    div[role="radiogroup"] label:hover::before {
        opacity: 0.30 !important;
        transform: scale(1.04) !important;
    }

    div[role="radiogroup"] label:hover p,
    div[role="radiogroup"] label:hover span {
        color: #FFFFFF !important;
        text-shadow: 0 0 5px rgba(236, 72, 153, 0.25) !important;
    }

    /* Selected option */
    div[role="radiogroup"] label:has(input:checked) {
        border-color: #C084FC !important;
        background: linear-gradient(
            110deg,
            rgba(139, 92, 246, 0.25),
            rgba(236, 72, 153, 0.20)
        ) !important;
        box-shadow:
            0 0 12px rgba(139, 92, 246, 0.25),
            inset 0 0 10px rgba(236, 72, 153, 0.08) !important;
    }

    div[role="radiogroup"] label:has(input:checked)::before {
        opacity: 0.35 !important;
        transform: scale(1.04) !important;
    }

    /* Keyboard accessibility */
    div[role="radiogroup"] label:focus-within {
        outline: 2px solid #EC4899 !important;
        outline-offset: 3px !important;
    }


    /* NEXUS — WHITE SIDEBAR COLLAPSE ICON */
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        color: #FFFFFF !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg path,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg path {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
        opacity: 1 !important;
        filter: none !important;
    }

    /* Keep the sidebar toggle visible on hover */
    [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover {
        color: #FFFFFF !important;
        opacity: 1 !important;
    }


    </style>

    """,
    unsafe_allow_html=True,
)


# Light mode theme overrides
if st.session_state.get("light_mode", False):
    st.markdown(
        """
        <style>
        /* Main background */
        .stApp {
            background: #F4F7FB !important;
            color: #172033 !important;
        }

        /* Main content */
        .stApp h1,
        .stApp h2,
        .stApp h3 {
            color: #172033 !important;
            text-shadow: none !important;
        }

        .stApp p,
        .stApp label,
        .stApp [data-testid="stCaptionContainer"] {
            color: #526176 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #FFFFFF !important;
            border-right: 1px solid #D9E2EF !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #075985 !important;
        }

        /* Cards */
        [data-testid="stMetric"] {
            background: #FFFFFF !important;
            border: 1px solid #D9E2EF !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05) !important;
        }

        [data-testid="stMetricLabel"] {
            color: #526176 !important;
        }

        [data-testid="stMetricValue"] {
            color: #075985 !important;
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            color: #172033 !important;
            border-color: #CBD5E1 !important;
        }

        /* Tables and charts */
        [data-testid="stDataFrame"],
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"] {
            background: #FFFFFF !important;
            border-color: #D9E2EF !important;
        }

        /* Navigation text */
        div[role="radiogroup"] label p,
        div[role="radiogroup"] label span {
            color: #172033 !important;
            text-shadow: none !important;
        }

        div[role="radiogroup"] label {
            background: #FFFFFF !important;
            border-color: #D9E2EF !important;
        }

        div[role="radiogroup"] label:has(input:checked) {
            background: #E8EEFF !important;
            border-color: #7966FF !important;
        }

        /* Keep sidebar collapse icon white */
        [data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg {
            color: #FFFFFF !important;
            stroke: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_database():
    connection = sqlite3.connect("tickets.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            employee_name TEXT NOT NULL,
            issue_title TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    columns = [
        column[1]
        for column in connection.execute(
            "PRAGMA table_info(tickets)"
        ).fetchall()
    ]

    if "category" not in columns:
        connection.execute(
            "ALTER TABLE tickets ADD COLUMN category TEXT DEFAULT 'Other'"
        )

    if "created_at" not in columns:
        connection.execute(
        "ALTER TABLE tickets ADD COLUMN created_at TEXT"
    )

    if "updated_at" not in columns:
        connection.execute(
        "ALTER TABLE tickets ADD COLUMN updated_at TEXT"
    )

    if "resolved_at" not in columns:
        connection.execute(
        "ALTER TABLE tickets ADD COLUMN resolved_at TEXT"
    )

    connection.execute(
    """
    UPDATE tickets
    SET created_at = CURRENT_TIMESTAMP
    WHERE created_at IS NULL
    """
    )

    connection.execute(
    """
    UPDATE tickets
    SET updated_at = created_at
    WHERE updated_at IS NULL
    """
    )

    connection.commit()
    connection.close()


create_database()


with st.sidebar:



    st.markdown("# NEXUS")
    st.caption("IT SERVICE DESK")
            
    # Theme switch
    if "light_mode" not in st.session_state:
        st.session_state.light_mode = False

    st.toggle(
        "☀️ Light Mode",
        key="light_mode"
    )
    st.divider()

    st.markdown("### Workspace")


    selected_page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Create Ticket",
            "Manage Tickets",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )


    st.divider()
    st.caption("SERVICE DESK PORTAL")
    st.caption("IT Support Operations")


# with st.sidebar:
#     st.markdown("# NEXUS")
#     st.caption("IT SERVICE DESK")
#     st.divider()

#     st.markdown("### Workspace")
#     st.markdown("Monitor and manage IT support requests.")

#     st.divider()
#     st.caption("SERVICE DESK PORTAL")
#     st.caption("Ticket Operations")
#     st.caption("Analytics & Reporting")
#     st.caption("System Administration")


# Theme-aware Plotly chart colors
if st.session_state.get("light_mode", False):
    chart_text = "#334155"
    chart_grid = "rgba(100, 116, 139, 0.18)"
    chart_axis = "rgba(100, 116, 139, 0.40)"
    chart_plot_bg = "rgba(255, 255, 255, 0.0)"
    resolution_color = "#0D9488"
    category_color = "#7966CC"
    priority_color = "#D97706"
else:
    chart_text = "#E6F7FF"
    chart_grid = "rgba(200, 215, 230, 0.20)"
    chart_axis = "rgba(200, 215, 230, 0.35)"
    chart_plot_bg = "rgba(13, 20, 36, 0.55)"
    resolution_color = "#00F5A0"
    category_color = "#7966FF"
    priority_color = "#FF9F43"


st.title(f"Nexus | {selected_page}")
st.caption("Centralized IT support and ticket operations")
st.divider()

# st.title("IT Help Desk Ticket Management System")
if selected_page == "Dashboard":
    st.write("Monitor support requests, ticket status, and service desk activity.")
    
if selected_page == "Create Ticket":

    st.header("Create Support Ticket")
    st.write("Please provide details about the IT issue you are experiencing.")

    employee_name = st.text_input("Employee Name")
    issue_title = st.text_input("Issue Title")
    issue_description = st.text_area("Describe the IT Issue")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    category = st.selectbox(
    "Issue Category",
    ["Hardware", "Software", "Network", "Access", "Other"])

    # if st.button("Submit Ticket"):
    #     st.success("Button clicked! Ticket submission is ready to be implemented.")

    if st.button("Submit Ticket"):
        if not employee_name.strip():
            st.error("Please enter your name.")
        elif not issue_title.strip():
            st.error("Please enter an issue title.")
        elif not issue_description.strip():
            st.error("Please describe the IT issue.")
        else:
            ticket_id = str(uuid.uuid4())[:8].upper()

            connection = sqlite3.connect("tickets.db")

            connection.execute(
                """
                INSERT INTO tickets
                (ticket_id, employee_name, issue_title, issue_description, priority, status, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    ticket_id,
                    employee_name.strip(),
                    issue_title.strip(),
                    issue_description.strip(),
                    priority,
                    "Open",
                    category,
                ),
            )

            connection.commit()
            connection.close()

            st.success(f"Ticket submitted successfully! Your Ticket ID is: {ticket_id}")
        
        # ticket_id = str(uuid.uuid4())[:8].upper()
        # st.success(f"Ticket submitted successfully! Your Ticket ID is: {ticket_id}")


if selected_page == "Manage Tickets":

    st.header("View Support Tickets")

    
    search_query = st.text_input(
        "Search Tickets",
        placeholder="Enter ticket ID or issue title...",
    )

    filter_status = st.selectbox(
        "Filter by Status",
        ["All", "Open", "In Progress", "Resolved"],
    )

    filter_priority = st.selectbox(
        "Filter by Priority",
        ["All", "Low", "Medium", "High"],
    )

    filter_category = st.selectbox(
        "Filter by Category",
        ["All", "Hardware", "Software", "Network", "Access", "Other"],
    )


    connection = sqlite3.connect("tickets.db")

    tickets = connection.execute(
        "SELECT * FROM tickets ORDER BY rowid DESC"
    ).fetchall()



    connection.close()

    
    search_text = search_query.strip().lower()

    filtered_tickets = []

    for ticket in tickets:
        ticket_id = ticket[0].lower()
        issue_title = ticket[2].lower()
        ticket_priority = ticket[4]
        ticket_status = ticket[5]

        matches_search = (
            search_text in ticket_id
            or search_text in issue_title
        )

        matches_status = (
            filter_status == "All"
            or ticket_status == filter_status
        )

        matches_priority = (
            filter_priority == "All"
            or ticket_priority == filter_priority
        )

        ticket_category = ticket[6]

        matches_category = (
            filter_category == "All"
            or ticket_category == filter_category
        )

        if (
            matches_search
            and matches_status
            and matches_priority
            and matches_category
        ):
            filtered_tickets.append(ticket)


    # if tickets:
    #     st.dataframe(
    #         tickets,
    #         column_config={
    #             "ticket_id": "Ticket ID",
    #             "employee_name": "Employee Name",
    #             "issue_title": "Issue Title",
    #             "issue_description": "Description",
    #             "priority": "Priority",
    #             "status": "Status",
    #         },
    #     )
    # else:
    #     st.info("No tickets have been submitted yet.")

    if filtered_tickets:
        # st.dataframe(
        #     tickets,
        #     column_config={
        #         "ticket_id": "Ticket ID",
        #         "employee_name": "Employee Name",
        #         "issue_title": "Issue Title",
        #         "issue_description": "Description",
        #         "priority": "Priority",
        #         "status": "Status",
        #     },
        # )

        # st.dataframe(
        #     filtered_tickets,
        #     column_config={
        #         0: st.column_config.TextColumn("Ticket ID"),
        #         1: st.column_config.TextColumn("Employee Name"),
        #         2: st.column_config.TextColumn("Issue Title"),
        #         3: st.column_config.TextColumn("Description"),
        #         4: st.column_config.TextColumn("Priority"),
        #         5: st.column_config.TextColumn("Status"),
        #         6: st.column_config.TextColumn("Category"),
        #     },
        #     hide_index=True,
        #     use_container_width=True,
        # )
        # display_tickets = [
        #     {
        #         "Ticket ID": ticket[0],
        #         "Employee Name": ticket[1],
        #         "Issue Title": ticket[2],
        #         "Description": ticket[3],
        #         "Priority": ticket[4],
        #         "Status": ticket[5],
        #         "Category": ticket[6],
        #         "Created At": ticket[7][:16] if ticket[7] else "",
        #         "Last Updated": ticket[8][:16] if ticket[8] else "",
        #         "Resolved At": ticket[9][:16] if ticket[9] else "",
        #     }
        #     for ticket in filtered_tickets
        # ]
        
        display_tickets = [
            {
                "Ticket ID": ticket[0],
                "Employee Name": ticket[1],
                "Issue Title": ticket[2],
                "Description": ticket[3],
                "Priority": ticket[4],
                "Status": ticket[5],
                "Category": ticket[6],
                "Created At": format_ist(ticket[7]),
                "Last Updated": format_ist(ticket[8]),
                "Resolved At": format_ist(ticket[9]),
                "SLA Deadline": (
                    calculate_sla(ticket[4], ticket[7]).strftime("%Y-%m-%d %H:%M")
                    if ticket[7] else ""
                ),
                "SLA Status": check_sla_status(
                    ticket[4], ticket[7], ticket[5]
                ),
            }
            for ticket in filtered_tickets
        ]


        st.dataframe(
            display_tickets,
            hide_index=True,
            use_container_width=True,
        )
            
        csv_data = pd.DataFrame(display_tickets).to_csv(index=False)

        st.download_button(
            label="📥 Export Tickets to CSV",
            data=csv_data,
            file_name="nexus_tickets.csv",
            mime="text/csv",
        )
    else:
        st.info("No tickets have been submitted yet.")


    st.header("Update Ticket Status")

    connection = sqlite3.connect("tickets.db")
    ticket_options = connection.execute(
        "SELECT ticket_id, issue_title, status FROM tickets ORDER BY rowid DESC"
    ).fetchall()
    connection.close()

    if ticket_options:
        ticket_ids = [ticket[0] for ticket in ticket_options]

        selected_ticket = st.selectbox(
            "Select a ticket",
            ticket_ids,
            format_func=lambda ticket_id: next(
                f"{ticket[0]} - {ticket[1]} ({ticket[2]})"
                for ticket in ticket_options
                if ticket[0] == ticket_id
            ),
        )

        new_status = st.selectbox(
            "New Status",
            ["Open", "In Progress", "Resolved"],
        )

        if st.button("Update Status"):
            connection = sqlite3.connect("tickets.db")
            connection.execute(
                " UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP, resolved_at = CASE WHEN ? = 'Resolved' THEN CURRENT_TIMESTAMP ELSE NULL END WHERE ticket_id = ?",
                (new_status, new_status, selected_ticket),
            )
            connection.commit()
            connection.close() 

            st.success(f"Ticket {selected_ticket} updated to {new_status}!")
            st.rerun()
    else:
        st.info("No tickets available to update.")


if selected_page == "Dashboard":

    st.header("Help Desk Dashboard")

    connection = sqlite3.connect("tickets.db")

    total_tickets = connection.execute(
        "SELECT COUNT(*) FROM tickets"
    ).fetchone()[0]

    open_tickets = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'Open'"
    ).fetchone()[0]

    in_progress_tickets = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved_tickets = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'"
    ).fetchone()[0]

    
    sla_breached_tickets = connection.execute(
        """
        SELECT COUNT(*)
        FROM tickets
        WHERE status != 'Resolved'
        AND created_at IS NOT NULL
        AND datetime('now', 'localtime') >
            datetime(
                created_at,
                CASE priority
                    WHEN 'High' THEN '+4 hours'
                    WHEN 'Medium' THEN '+8 hours'
                    WHEN 'Low' THEN '+24 hours'
                    ELSE '+24 hours'
                END
            )
        """
    ).fetchone()[0]

    resolved_within_sla = connection.execute(
        """
        SELECT COUNT(*)
        FROM tickets
        WHERE status = 'Resolved'
        AND resolved_at IS NOT NULL
        AND created_at IS NOT NULL
        AND datetime(resolved_at) <=
            datetime(
                created_at,
                CASE priority
                    WHEN 'High' THEN '+4 hours'
                    WHEN 'Medium' THEN '+8 hours'
                    WHEN 'Low' THEN '+24 hours'
                    ELSE '+24 hours'
                END
            )
        """
    ).fetchone()[0]

    
    resolved_after_sla = connection.execute(
        """
        SELECT COUNT(*)
        FROM tickets
        WHERE status = 'Resolved'
        AND resolved_at IS NOT NULL
        AND created_at IS NOT NULL
        AND datetime(resolved_at) >
            datetime(
                created_at,
                CASE priority
                    WHEN 'High' THEN '+4 hours'
                    WHEN 'Medium' THEN '+8 hours'
                    WHEN 'Low' THEN '+24 hours'
                    ELSE '+24 hours'
                END
            )
        """
    ).fetchone()[0]


    resolved_with_timestamp = connection.execute(
        """
        SELECT COUNT(*)
        FROM tickets
        WHERE status = 'Resolved'
        AND resolved_at IS NOT NULL
        AND created_at IS NOT NULL
        """
    ).fetchone()[0]

    sla_compliance = (
        (resolved_within_sla / resolved_with_timestamp) * 100
        if resolved_with_timestamp > 0
        else 0
    )

    category_counts = connection.execute(
        """
        SELECT category, COUNT(*)
        FROM tickets
        GROUP BY category
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()

    priority_counts = connection.execute(
        """
        SELECT priority, COUNT(*)
        FROM tickets
        GROUP BY priority
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()

    connection.close()


    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tickets", total_tickets)
    col2.metric("Open", open_tickets)
    col3.metric("In Progress", in_progress_tickets)
    col4.metric("Resolved", resolved_tickets)

    col5, col6 = st.columns(2)

    col5.metric("SLA Breached", sla_breached_tickets)
    col6.metric("SLA Compliance", f"{sla_compliance:.1f}%")

    
    st.divider()
    st.subheader("Resolution Performance")

    resolution_chart_data = {
        "Resolution Result": [
            "Within SLA",
            "After SLA",
        ],
        "Number of Tickets": [
            resolved_within_sla,
            resolved_after_sla,
        ],
    }

    # st.bar_chart(
    #     resolution_chart_data,
    #     x="Resolution Result",
    #     y="Number of Tickets",
    # )


    # fig = px.bar(
    #     resolution_chart_data,
    #     x="Resolution Result",
    #     y="Number of Tickets",
    #     color_discrete_sequence=["#00F5A0"],
    # )


    # fig.update_layout(
    #     paper_bgcolor="rgba(0,0,0,0)",
    #     plot_bgcolor="rgba(13,20,36,0.55)",
    #     font_color="#FFFFFF",
    #     xaxis_title="Priority",
    #     yaxis_title="Number of Tickets",
    #     xaxis=dict(
    #         title_font=dict(color="#FFFFFF"),
    #         tickfont=dict(color="#FFFFFF"),
    #         showgrid=True,
    #         gridcolor="rgba(200,215,230,0.25)",
    #         zerolinecolor="rgba(200,215,230,0.35)",
    #         linecolor="rgba(200,215,230,0.35)",
    #     ),
    #     yaxis=dict(
    #         title_font=dict(color="#FFFFFF"),
    #         tickfont=dict(color="#FFFFFF"),
    #         showgrid=True,
    #         gridcolor="rgba(200,215,230,0.25)",
    #         zerolinecolor="rgba(200,215,230,0.35)",
    #         linecolor="rgba(200,215,230,0.35)",
    #     ),
    # )

    # st.plotly_chart(fig, use_container_width=True)

    
    fig = px.bar(
        resolution_chart_data,
        x="Resolution Result",
        y="Number of Tickets",
        color_discrete_sequence=[resolution_color],
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=chart_plot_bg,
        font=dict(color=chart_text),
        xaxis_title="Resolution Result",
        yaxis_title="Number of Tickets",
        xaxis=dict(
            title_font=dict(color=chart_text),
            tickfont=dict(color=chart_text),
            showgrid=True,
            gridcolor=chart_grid,
            zerolinecolor=chart_axis,
            linecolor=chart_axis,
        ),
        yaxis=dict(
            title_font=dict(color=chart_text),
            tickfont=dict(color=chart_text),
            showgrid=True,
            gridcolor=chart_grid,
            zerolinecolor=chart_axis,
            linecolor=chart_axis,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


    


    st.divider()
    st.subheader("Ticket Category Breakdown")

    if category_counts:
        category_chart_data = {
            "Category": [
                row[0] if row[0] else "Other"
                for row in category_counts
            ],
            "Number of Tickets": [
                row[1] for row in category_counts
            ],
        }

       
        fig = px.bar(
            category_chart_data,
            x="Category",
            y="Number of Tickets",
            color_discrete_sequence=[category_color],
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=chart_plot_bg,
            font=dict(color=chart_text),
            xaxis_title="Category",
            yaxis_title="Number of Tickets",
            xaxis=dict(
                title_font=dict(color=chart_text),
                tickfont=dict(color=chart_text),
                showgrid=True,
                gridcolor=chart_grid,
                zerolinecolor=chart_axis,
                linecolor=chart_axis,
            ),
            yaxis=dict(
                title_font=dict(color=chart_text),
                tickfont=dict(color=chart_text),
                showgrid=True,
                gridcolor=chart_grid,
                zerolinecolor=chart_axis,
                linecolor=chart_axis,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        # st.bar_chart(
        #     category_chart_data,
        #     x="Category",
        #     y="Number of Tickets",
        #     color="#7966FF",
        #     horizontal=False,
        #     height=350,
        # )
    else:
        st.info("No ticket category data available yet.")


    st.divider()
    st.subheader("Ticket Priority Breakdown")

    if priority_counts:
        priority_chart_data = {
            "Priority": [
                row[0] for row in priority_counts
            ],
            "Number of Tickets": [
                row[1] for row in priority_counts
            ],
        }


        fig = px.bar(
            priority_chart_data,
            x="Priority",
            y="Number of Tickets",
            color_discrete_sequence=[priority_color],
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=chart_plot_bg,
            font=dict(color=chart_text),
            xaxis_title="Priority",
            yaxis_title="Number of Tickets",
            xaxis=dict(
                title_font=dict(color=chart_text),
                tickfont=dict(color=chart_text),
                showgrid=True,
                gridcolor=chart_grid,
                zerolinecolor=chart_axis,
                linecolor=chart_axis,
            ),
            yaxis=dict(
                title_font=dict(color=chart_text),
                tickfont=dict(color=chart_text),
                showgrid=True,
                gridcolor=chart_grid,
                zerolinecolor=chart_axis,
                linecolor=chart_axis,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No ticket priority data available yet.")


