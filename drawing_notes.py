import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Drawing Notes Generator", page_icon="📐", layout="wide")

# Custom CSS for color #1BA099 with stronger selectors
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

/* Clear button */
.stButton > button {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
    color: white !important;
}

.stButton > button:hover {
    background-color: #c82333 !important;
    border-color: #bd2130 !important;
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

# Initialize session state for selected notes
if 'selected_notes' not in st.session_state:
    st.session_state.selected_notes = []
if 'selected_indices' not in st.session_state:
    st.session_state.selected_indices = set()

# Create type selector
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Type Selection")

    # Get unique types
    types = df['Type'].unique().tolist()
    types.sort()

    # Type selector
    selected_type = st.selectbox(
        "Part/Assembly type:",
        options=["All"] + types,
        index=0
    )

    # Filter notes by type
    if selected_type == "All":
        filtered_notes = df
    else:
        filtered_notes = df[df['Type'] == selected_type]

    st.info(f"**{len(filtered_notes)}** notes available")

    # Clear button
    if st.button("🗑️ Clear All Notes", use_container_width=True):
        st.session_state.selected_notes = []
        st.session_state.selected_indices = set()
        st.rerun()

with col2:
    st.subheader("Select Notes")

    # Show checkboxes for each note
    for idx, row in filtered_notes.iterrows():
        # Check if this note is already selected
        is_checked = idx in st.session_state.selected_indices

        if st.checkbox(f"**{row['Name']}** ({row['Type']})", 
                      key=f"check_{idx}", 
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

st.markdown("---")

# Generate final text
if st.session_state.selected_notes:
    st.subheader("📝 Generated Notes")

    # Show selected notes count
    st.info(f"**{len(st.session_state.selected_notes)}** notes selected")

    # Combine all selected notes in order
    final_text = "\n\n".join([note['text'] for note in st.session_state.selected_notes])

    # Create custom HTML component with blueprint style
    st.components.v1.html(
        f"""
        <div style="position: relative;">
            <textarea id="textToCopy" style="
                width: 100%; 
                height: 300px; 
                padding: 10px; 
                font-family: 'Courier New', monospace; 
                font-size: 14px; 
                background-color: #003559;
                color: #FFFFFF;
                border: 2px solid #006DAA;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 109, 170, 0.3);
            ">{final_text}</textarea>
            <button onclick="copyToClipboard()" style="
                margin-top: 10px; 
                background-color: #1BA099; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px; 
                transition: background-color 0.3s;
            ">
                📋 Copy to Clipboard
            </button>
            <span id="copyMessage" style="margin-left: 10px; color: #1BA099; font-weight: bold;"></span>
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
        height=400
    )

    # Download button
    st.download_button(
        label="💾 Download as TXT",
        data=final_text,
        file_name="drawing_notes.txt",
        mime="text/plain",
        use_container_width=False
    )

else:
    st.info("👈 Select at least one note from the left to generate text")

# Footer
st.markdown("---")
st.caption("🔧 Atlantis Prototyping - Drawing Notes Generator")
