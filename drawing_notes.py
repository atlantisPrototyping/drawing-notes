import streamlit as st
import pandas as pd
import re
import requests
from datetime import datetime, timezone

# Page configuration with custom favicon
st.set_page_config(
    page_title="Drawing Notes Generator", 
    page_icon="logoSimpleVerde.png",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
/* Force checkbox color when checked */
input[type="checkbox"] {
    accent-color: #1BA099 !important;
}

/* Download button color */
.stDownloadButton > button {
    background-color: #1BA099 !important;
    border-color: #1BA099 !important;
    color: white !important;
}

.stDownloadButton > button:hover {
    background-color: #158a82 !important;
    border-color: #158a82 !important;
}

/* Submit button color */
div.stButton > button:first-child {
    background-color: #1BA099 !important;
    color: white !important;
    border: none !important;
}

div.stButton > button:first-child:hover {
    background-color: #158a82 !important;
    color: white !important;
}

/* Compact spacing */
.stCheckbox {
    margin-bottom: 0.25rem !important;
    padding: 0.25rem 0 !important;
}

div[data-testid="column"] {
    padding: 0.5rem !important;
}

/* Make headers more compact but visible */
h1 {
    margin-top: 0.75rem !important;
    margin-bottom: 0.75rem !important;
    padding-top: 0.25rem !important;
    font-size: 2.2rem !important;
    line-height: 1.3 !important;
}

h3 {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    font-size: 1.2rem !important;
}

/* Compact horizontal rule */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.75rem !important;
}

/* Compact selectbox */
.stSelectbox {
    margin-bottom: 0.5rem !important;
}

/* Reduce top padding of main block */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
}

/* Logo styling */
.logo-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

.logo-container a {
    display: inline-block;
    line-height: 0;
}
</style>
""", unsafe_allow_html=True)

# Notion API configuration
NOTION_TOKEN = st.secrets.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = st.secrets.get("NOTION_DATABASE_ID", "")
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# ---------- Notion helpers ----------
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

def find_page_by_email(email: str):
    """
    Busca una página en la base de datos por el valor de la propiedad Email.
    Devuelve el page_id si la encuentra, si no devuelve None.
    """
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return None
    url = f"{NOTION_API_URL}/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Email",
            "email": {
                "equals": email
            }
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=notion_headers())
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        return results[0]["id"]
    except Exception:
        return None

def build_usage_block(timestamp_iso: str,
                     num_notes: int,
                     note_types: str,
                     has_specify: bool) -> list:
    """
    Construye los bloques de contenido para un uso de la app.
    Devuelve una lista de bloques Notion: [divider, paragraph].
    """
    dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    human_ts = dt.strftime("%Y-%m-%d %H:%M UTC")

    text_lines = [
        f"**Date:** {human_ts}",
        f"**Notes generated:** {num_notes}",
        f"**Note types used:** {note_types}",
        f"**Requires editing:** {'Yes (contains [specify] fields)' if has_specify else 'No'}",
    ]

    text_block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "\n".join(text_lines)}
                }
            ]
        }
    }

    divider_block = {
        "object": "block",
        "type": "divider",
        "divider": {}
    }

    return [divider_block, text_block]

def create_lead_page(name, email, num_notes, note_types, has_specify):
    """
    Crea una nueva página en la base de datos con:
    - Propiedades: Name, Email, App Source
    - Contenido: histórico de usos (primer uso)
    """
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return False

    url = f"{NOTION_API_URL}/pages"
    now_utc = datetime.now(timezone.utc).isoformat()

    children_blocks = build_usage_block(
        timestamp_iso=now_utc,
        num_notes=num_notes,
        note_types=note_types,
        has_specify=has_specify,
    )

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {"text": {"content": name}}
                ]
            },
            "Email": {
                "email": email
            },
            "App Source": {
                "select": {
                    "name": "Drawing notes"
                }
            },
        },
        "children": children_blocks
    }

    try:
        resp = requests.post(url, json=payload, headers=notion_headers())
        return resp.status_code in (200, 201)
    except Exception:
        return False

def append_usage_to_page(page_id, num_notes, note_types, has_specify):
    """
    Añade un nuevo bloque de uso (divider + texto) al final de una página existente.
    """
    if not NOTION_TOKEN:
        return False

    url = f"{NOTION_API_URL}/blocks/{page_id}/children"
    now_utc = datetime.now(timezone.utc).isoformat()

    children_blocks = build_usage_block(
        timestamp_iso=now_utc,
        num_notes=num_notes,
        note_types=note_types,
        has_specify=has_specify,
    )

    payload = {
        "children": children_blocks
    }

    try:
        resp = requests.patch(url, json=payload, headers=notion_headers())
        return resp.status_code in (200, 201)
    except Exception:
        return False

def add_to_notion(name, email, num_notes, note_types, has_specify):
    """
    Lógica principal:
    - Si ya hay una página para ese email → añade entrada nueva en la nota.
    - Si no existe → crea página nueva con Name, Email y App Source.
    """
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return False

    page_id = find_page_by_email(email)
    if page_id:
        return append_usage_to_page(
            page_id=page_id,
            num_notes=num_notes,
            note_types=note_types,
            has_specify=has_specify,
        )
    else:
        return create_lead_page(
            name=name,
            email=email,
            num_notes=num_notes,
            note_types=note_types,
            has_specify=has_specify,
        )

# Header with title and logo
header_col1, header_col2 = st.columns([2, 1])

with header_col1:
    st.title("📐 Drawing Notes Generator")

with header_col2:
    logo_html = """
    <div class="logo-container">
        <a href="https://www.atlantisprototyping.com" target="_blank">
            <img src="app/static/logoVerde.png" width="200">
        </a>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

st.markdown("---")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('drawing_notes.csv', encoding='utf-8-sig')

df = load_data()

# Define logical order for drawing notes
TYPE_ORDER = {
    'General': 0,
    'Tolerances': 1,
    'Metalic': 2,
    'Sheetmetal': 3,
    'Tube': 4,
    'Weld': 5,
    'Heat Treatment': 6,
    'Surface Treatment': 7,
    'Assembly': 8,
    'Inspection': 9
}

# Initialize session state
if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = set()
if 'clear_trigger' not in st.session_state:
    st.session_state.clear_trigger = 0

# Two main columns
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("Select Notes")

    # Type selector
    types = df['Type'].unique().tolist()
    types.sort(key=lambda x: TYPE_ORDER.get(x, 999))

    selected_type = st.selectbox(
        "Filter by type:",
        options=["All"] + types,
        index=0
    )

    # Filter notes by type
    if selected_type == "All":
        filtered_notes = df
    else:
        filtered_notes = df[df['Type'] == selected_type]

    # Container with fixed height
    with st.container(height=560):
        for idx, row in filtered_notes.iterrows():
            is_checked = idx in st.session_state.selected_indices
            checkbox_key = f"check_{idx}_{st.session_state.clear_trigger}"

            # Check if note contains [specify] placeholders
            has_specify = '[specify' in row['Text'].lower()
            label = f"**{row['Name']}** ({row['Type']})"
            if has_specify:
                label = f"⚠️ **{row['Name']}** ({row['Type']}) *- needs editing*"

            if st.checkbox(label, key=checkbox_key, value=is_checked):
                st.session_state.selected_indices.add(idx)
            else:
                st.session_state.selected_indices.discard(idx)

with col_right:
    st.subheader("Generated Notes")

    # Determine what text to show
    if st.session_state.selected_indices:
        selected_notes_data = []
        has_specify_fields = False

        for idx in st.session_state.selected_indices:
            row = df.iloc[idx]
            text = row['Text']

            # Check if this note has [specify] fields
            if '[specify' in text.lower():
                has_specify_fields = True

            selected_notes_data.append({
                'index': idx,
                'text': text,
                'name': row['Name'],
                'type': row['Type'],
                'type_order': TYPE_ORDER.get(row['Type'], 999),
                'original_index': idx
            })

        selected_notes_data.sort(key=lambda x: (x['type_order'], x['original_index']))
        final_text = "\n\n".join([note['text'] for note in selected_notes_data])
        show_buttons = True

        # Store generation info in session state for Notion
        types_used = list(set([note['type'] for note in selected_notes_data]))
        types_used.sort(key=lambda x: TYPE_ORDER.get(x, 999))
        st.session_state['last_generation'] = {
            'num_notes': len(selected_notes_data),
            'note_types': ", ".join(types_used),
            'has_specify': has_specify_fields
        }
    else:
        final_text = "👈 Select notes from the left panel"
        show_buttons = False
        has_specify_fields = False

    # Warning message if there are [specify] fields
    warning_html = ""
    if show_buttons and has_specify_fields:
        warning_html = """
            <div style="
                background-color: #FFA50080;
                border-left: 4px solid #FF8C00;
                padding: 12px 15px;
                margin-bottom: 10px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="font-size: 20px;">⚠️</span>
                <div>
                    <strong style="color: #FF8C00; font-size: 15px;">Action Required</strong>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #333;">
                        Some notes contain <strong>[specify]</strong> placeholders. 
                        Please edit these fields according to your requirements before using.
                    </p>
                </div>
            </div>
        """

    button_section = ""
    if show_buttons:
        button_section = f"""
            {warning_html}
            <div style="margin-top: 10px; display: flex; gap: 10px; align-items: center;">
                <button onclick="copyToClipboard()" style="
                    background-color: #1BA099; 
                    color: white; 
                    padding: 10px 20px; 
                    border: none; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 15px; 
                    font-weight: 500;
                    transition: background-color 0.3s;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                ">
                    📋 Copy to Clipboard
                </button>
                <span id="copyMessage" style="
                    color: #1BA099; 
                    font-weight: 600;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    font-size: 14px;
                "></span>
            </div>
        """

    # Textarea with scrollbar
    st.components.v1.html(
        f"""
        <style>
        .textarea-container {{
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }}

        #textToCopy {{
            overflow-y: scroll !important;
            box-sizing: border-box !important;
            scrollbar-width: thin !important;
            scrollbar-color: #1BA099 #001F33 !important;
        }}

        #textToCopy::-webkit-scrollbar {{
            width: 16px !important;
            background: #001F33 !important;
        }}

        #textToCopy::-webkit-scrollbar-track {{
            background: #001F33 !important;
            border-left: 2px solid #006DAA !important;
        }}

        #textToCopy::-webkit-scrollbar-thumb {{
            background: #1BA099 !important;
            border: 3px solid #001F33 !important;
            border-radius: 8px !important;
            min-height: 40px !important;
        }}

        #textToCopy::-webkit-scrollbar-thumb:hover {{
            background: #25D5CA !important;
        }}

        #textToCopy::-webkit-scrollbar-thumb:active {{
            background: #158a82 !important;
        }}
        </style>

        <div class="textarea-container">
            <textarea id="textToCopy" style="
                width: calc(100% - 4px);
                height: 500px; 
                padding: 12px;
                margin: 0;
                font-family: 'Courier New', monospace; 
                font-size: 13px; 
                line-height: 1.5;
                background-color: #003559;
                color: #FFFFFF;
                border: 2px solid #006DAA;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 109, 170, 0.3);
                resize: vertical;
                overflow-y: scroll;
                box-sizing: border-box;
                {'text-align: center; padding-top: 230px; font-size: 16px;' if not show_buttons else ''}
            " {'readonly' if not show_buttons else ''}>{final_text}</textarea>
            {button_section}
        </div>

        <script>
        // Force scrollbar visibility
        window.addEventListener('load', function() {{
            const textarea = document.getElementById('textToCopy');
            textarea.style.display = 'none';
            textarea.offsetHeight;
            textarea.style.display = 'block';
        }});

        const buttons = document.querySelectorAll('button');

        if (buttons.length > 0) {{
            buttons[0].addEventListener('mouseenter', function() {{
                this.style.backgroundColor = '#158a82';
            }});
            buttons[0].addEventListener('mouseleave', function() {{
                this.style.backgroundColor = '#1BA099';
            }});
        }}

        function copyToClipboard() {{
            const text = document.getElementById('textToCopy').value;

            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(function() {{
                    document.getElementById('copyMessage').textContent = '✅ Copied!';
                    setTimeout(function() {{
                        document.getElementById('copyMessage').textContent = '';
                    }}, 2000);
                }}, function(err) {{
                    document.getElementById('copyMessage').textContent = '❌ Copy failed';
                }});
            }} else {{
                const textArea = document.getElementById('textToCopy');
                textArea.select();
                try {{
                    document.execCommand('copy');
                    document.getElementById('copyMessage').textContent = '✅ Copied!';
                    setTimeout(function() {{
                        document.getElementById('copyMessage').textContent = '';
                    }}, 2000);
                }} catch (err) {{
                    document.getElementById('copyMessage').textContent = '❌ Copy failed';
                }}
            }}
        }}
        </script>
        """,
        height=640
    )

    # Buttons below
    if show_buttons:
        col_download, col_clear, col_spacer = st.columns([1, 1, 2])

        with col_download:
            st.download_button(
                label="💾 Download as TXT",
                data=final_text,
                file_name="drawing_notes.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_clear:
            if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
                st.session_state.selected_indices = set()
                st.session_state.clear_trigger += 1
                st.rerun()

# ---------- CONTACT SECTION ----------
st.markdown("---")
st.subheader("Need Help or Developing Your Project?")
st.markdown("Leave your email and we'll contact you")

col_name, col_email = st.columns(2)
with col_name:
    user_name = st.text_input("Name (optional)", placeholder="John Doe", key="optional_name")
with col_email:
    user_email = st.text_input("Email (optional)", placeholder="john@example.com", key="optional_email")

# Submit contact info button
if st.button("Submit Contact Information", use_container_width=True):
    if user_email and user_name:
        # Validate email format
        if "@" in user_email and "." in user_email:
            # Use stored generation data if available
            if 'last_generation' in st.session_state:
                gen_data = st.session_state['last_generation']
                ok = add_to_notion(
                    user_name,
                    user_email,
                    gen_data['num_notes'],
                    gen_data['note_types'],
                    gen_data['has_specify']
                )
            else:
                # User hasn't generated notes yet
                ok = add_to_notion(
                    user_name,
                    user_email,
                    0,
                    "Interest - No notes generated",
                    False
                )

            if ok:
                st.success("✓ Your contact information has been saved. We'll be in touch soon!")
            else:
                st.error("Your information could not be saved. Please try again later.")
        else:
            st.error("Please enter a valid email address.")
    elif user_email or user_name:
        st.warning("Please provide both name and email to submit your information.")
    else:
        st.info("Please enter your name and email if you'd like us to contact you.")
