import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Drawing Notes Generator", page_icon="📐", layout="wide")

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

/* Compact spacing */
.stCheckbox {
    margin-bottom: 0.25rem !important;
    padding: 0.25rem 0 !important;
}

div[data-testid="column"] {
    padding: 0.5rem !important;
}

/* Make headers more compact */
h1 {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    padding-top: 0.5rem !important;
    font-size: 2rem !important;
}

h3 {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
    font-size: 1.2rem !important;
}

/* Compact horizontal rule */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Compact selectbox */
.stSelectbox {
    margin-bottom: 0.5rem !important;
}

/* Reduce top padding of main block */
.block-container {
    padding-top: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# Title (more compact)
st.title("📐 Drawing Notes Generator")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('drawing_notes.csv', encoding='utf-8-sig')

df = load_data()

# Define logical order for drawing notes (engineering drawing standard sequence)
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

# Two main columns: left for selection, right for text output
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

    # Use container with fixed height matching right side
    # Height = textarea (500px) + button section (~60px) = 560px total
    with st.container(height=560):
        for idx, row in filtered_notes.iterrows():
            is_checked = idx in st.session_state.selected_indices
            checkbox_key = f"check_{idx}_{st.session_state.clear_trigger}"

            if st.checkbox(f"**{row['Name']}** ({row['Type']})", 
                          key=checkbox_key, 
                          value=is_checked):
                st.session_state.selected_indices.add(idx)
            else:
                st.session_state.selected_indices.discard(idx)

with col_right:
    st.subheader("Generated Notes")

    # Determine what text to show
    if st.session_state.selected_indices:
        selected_notes_data = []
        for idx in st.session_state.selected_indices:
            row = df.iloc[idx]
            selected_notes_data.append({
                'index': idx,
                'text': row['Text'],
                'name': row['Name'],
                'type': row['Type'],
                'type_order': TYPE_ORDER.get(row['Type'], 999),
                'original_index': idx
            })

        selected_notes_data.sort(key=lambda x: (x['type_order'], x['original_index']))
        final_text = "\n\n".join([note['text'] for note in selected_notes_data])
        show_buttons = True
    else:
        final_text = "👈 Select notes from the left panel"
        show_buttons = False

    button_section = ""
    if show_buttons:
        button_section = """
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
        height=560
    )

    # Buttons below: Download and Clear side by side
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

# Footer
st.markdown("---")
st.caption("🔧 Atlantis Prototyping - Drawing Notes Generator")
