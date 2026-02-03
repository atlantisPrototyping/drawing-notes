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

# Initialize session state
if 'selected_notes' not in st.session_state:
    st.session_state.selected_notes = []
if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = set()
if 'clear_trigger' not in st.session_state:
    st.session_state.clear_trigger = 0

# Two main columns: left for selection, right for text output
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("Select Notes")

    # Type selector and clear button in same row
    col_select, col_clear = st.columns([2, 1])

    with col_select:
        # Get unique types
        types = df['Type'].unique().tolist()
        types.sort()

        # Type selector
        selected_type = st.selectbox(
            "Filter by type:",
            options=["All"] + types,
            index=0
        )

    with col_clear:
        # Clear button with proper spacing
        st.write("")  # Spacer for alignment
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.selected_notes = []
            st.session_state.selected_indices = set()
            st.session_state.clear_trigger += 1
            st.rerun()

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
            # Add to selected notes if not already there
            if idx not in st.session_state.selected_indices:
                st.session_state.selected_notes.append({
                    'index': idx,
                    'text': row['Text'],
                    'name': row['Name'],
                    'type': row['Type']
                })
                st.session_state.selected_indices.add(idx)
        else:
            # Remove from selected notes if unchecked
            if idx in st.session_state.selected_indices:
                st.session_state.selected_notes = [
                    note for note in st.session_state.selected_notes 
                    if note['index'] != idx
                ]
                st.session_state.selected_indices.remove(idx)

with col_right:
    st.subheader("Generated Notes")

    if st.session_state.selected_notes:
        # Combine all selected notes in order
        final_text = "\n\n".join([note['text'] for note in st.session_state.selected_notes])

        # Create custom HTML component with blueprint style
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
                    ">
                        📋 Copy to Clipboard
                    </button>
                    <span id="copyMessage" style="color: #1BA099; font-weight: bold;"></span>
                </div>
            </div>

            <script>
            // Add hover effect to button
            const btn = document.querySelector('button');
            btn.addEventListener('mouseenter', function() {{
                this.style.backgroundColor = '#158a82';
            }});
            btn.addEventListener('mouseleave', function() {{
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

        # Download button below
        st.download_button(
            label="💾 Download as TXT",
            data=final_text,
            file_name="drawing_notes.txt",
            mime="text/plain",
            use_container_width=False
        )

    else:
        st.info("👈 Select notes from the left panel")

# Footer
st.markdown("---")
st.caption("🔧 Atlantis Prototyping - Drawing Notes Generator")
