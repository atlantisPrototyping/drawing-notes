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
}

div[data-testid="column"] {
    padding: 0.5rem !important;
}

h3 {
    margin-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("📐 Drawing Notes Generator")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('drawing_notes.csv', encoding='utf-8-sig')

df = load_data()

# Define logical order for drawing notes (typical engineering drawing sequence)
TYPE_ORDER = {
    'General': 0,
    'Tolerances': 1,
    'Metalic': 2,
    'Sheetmetal': 3,
    'Tube': 4,
    'Weld': 5,
    'Assembly': 6,
    'Inspection': 7
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
    types.sort()

    # Type selector
    selected_type = st.selectbox(
        "Filter by type:",
        options=["All"] + types,
        index=0
    )

    st.markdown("---")

    # Filter notes by type
    if selected_type == "All":
        filtered_notes = df
    else:
        filtered_notes = df[df['Type'] == selected_type]

    # Show checkboxes for each note
    for idx, row in filtered_notes.iterrows():
        # Check if this note is already selected
        is_checked = idx in st.session_state.selected_indices

        # Use clear_trigger to force checkbox reset
        checkbox_key = f"check_{idx}_{st.session_state.clear_trigger}"

        if st.checkbox(f"**{row['Name']}** ({row['Type']})", 
                      key=checkbox_key, 
                      value=is_checked):
            st.session_state.selected_indices.add(idx)
        else:
            st.session_state.selected_indices.discard(idx)

with col_right:
    st.subheader("Generated Notes")

    if st.session_state.selected_indices:
        # Get selected notes from dataframe and sort by logical order
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

        # Sort by: 1) Type order, 2) Original CSV index
        selected_notes_data.sort(key=lambda x: (x['type_order'], x['original_index']))

        # Combine all selected notes in logical order
        final_text = "\n\n".join([note['text'] for note in selected_notes_data])

        # Create custom HTML component with blueprint style and aligned buttons
        st.components.v1.html(
            f"""
            <div style="position: relative;">
                <textarea id="textToCopy" style="
                    width: 100%; 
                    height: 450px; 
                    padding: 12px; 
                    font-family: 'Courier New', monospace; 
                    font-size: 13px; 
                    background-color: #003559;
                    color: #FFFFFF;
                    border: 2px solid #006DAA;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 109, 170, 0.3);
                    resize: vertical;
                ">{final_text}</textarea>
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
            </div>

            <script>
            // Add hover effects to button
            const copyBtn = document.querySelector('button');

            copyBtn.addEventListener('mouseenter', function() {{
                this.style.backgroundColor = '#158a82';
            }});
            copyBtn.addEventListener('mouseleave', function() {{
                this.style.backgroundColor = '#1BA099';
            }});

            function copyToClipboard() {{
                const text = document.getElementById('textToCopy').value;

                // Use modern Clipboard API
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
                    // Fallback for older browsers
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
            height=550
        )

        # Buttons below: Download and Clear side by side
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

    else:
        st.info("👈 Select notes from the left panel")

# Footer
st.markdown("---")
st.caption("🔧 Atlantis Prototyping - Drawing Notes Generator")
