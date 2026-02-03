import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Drawing Notes Generator", page_icon="📐", layout="wide")

# Custom CSS for color #1BA099
st.markdown("""
<style>
/* Checkbox color when checked */
.stCheckbox > label > div[data-testid="stMarkdownContainer"] > p {
    color: inherit;
}

/* Checkbox checked state */
input[type="checkbox"]:checked {
    background-color: #1BA099 !important;
    border-color: #1BA099 !important;
}

/* Primary button color */
.stDownloadButton > button {
    background-color: #1BA099 !important;
    border-color: #1BA099 !important;
}

.stDownloadButton > button:hover {
    background-color: #158a82 !important;
    border-color: #158a82 !important;
}

/* Selectbox focus */
.stSelectbox > div > div:focus-within {
    border-color: #1BA099 !important;
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

with col2:
    st.subheader("Select Notes")

    # Show checkboxes for each note
    selected_notes = []

    for idx, row in filtered_notes.iterrows():
        if st.checkbox(f"**{row['Name']}** ({row['Type']})", key=f"check_{idx}"):
            selected_notes.append(row['Text'])

st.markdown("---")

# Generate final text
if selected_notes:
    st.subheader("📝 Generated Notes")

    # Combine all selected notes
    final_text = "\n\n".join(selected_notes)

    # Create custom HTML component with copy button using Clipboard API
    st.components.v1.html(
        f"""
        <div style="position: relative;">
            <textarea id="textToCopy" style="width: 100%; height: 300px; padding: 10px; font-family: monospace; font-size: 14px; border: 1px solid #ddd; border-radius: 5px;">{final_text}</textarea>
            <button onclick="copyToClipboard()" style="margin-top: 10px; background-color: #1BA099; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                📋 Copy to Clipboard
            </button>
            <span id="copyMessage" style="margin-left: 10px; color: green; font-weight: bold;"></span>
        </div>

        <script>
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
