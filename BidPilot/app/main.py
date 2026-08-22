import streamlit as st
import time

# Set page config
st.set_page_config(page_title="BidPilot - RFP Agent", page_icon="🚀", layout="wide")

st.title("🚀 BidPilot")
st.subheader("Evidence-Grounded RFP Response & Compliance Agent")

# Sidebar for RFP Upload
with st.sidebar:
    st.header("📄 Upload RFP")
    uploaded_file = st.file_uploader("Drop your RFP PDF here", type=["pdf", "txt"])
    analyze_button = st.button("Analyze RFP", type="primary")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Requirements", "🧠 Evidence Mapping", "⚠️ Compliance", "✍️ Generated Response"])

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "user_override" not in st.session_state:
    st.session_state.user_override = False

if analyze_button and uploaded_file is not None:
    with st.spinner("Agent is extracting requirements..."):
        time.sleep(1.5)
        st.session_state.requirements = [
            {"id": "Req 1", "desc": "5+ years experience", "status": "SATISFIED", "evidence": "Company established in 2018."},
            {"id": "Req 2", "desc": "ISO 27001 certification", "status": "MISSING", "evidence": "No supporting document found."}
        ]
        
    with st.spinner("Agent is searching Knowledge Base for evidence..."):
        time.sleep(1.5)
        st.session_state.analysis_done = True
        st.session_state.user_override = False
        st.success("Analysis Complete!")

if st.session_state.analysis_done:
    with tab1:
        st.markdown("### Extracted Requirements")
        for req in st.session_state.requirements:
            st.info(f"**{req['id']}:** {req['desc']}")

    with tab2:
        st.markdown("### Evidence Mapping & Agent Reasoning")
        for req in st.session_state.requirements:
            st.markdown(f"#### {req['id']}\\n{req['desc']}")
            st.markdown(f"**Evidence:**\\n{req['evidence']}")
            
            # Show status override if applicable
            if req['id'] == "Req 2" and st.session_state.user_override:
                st.success("**Status:** ✅ SATISFIED (User Verified)")
            elif req['status'] == "SATISFIED":
                st.success("**Status:** ✅ SATISFIED")
            else:
                st.error("**Status:** ⚠️ MISSING INFORMATION\\n\\n**Action:** User verification required.")
            st.markdown("---")

    with tab3:
        st.markdown("### Compliance Audit")
        
        if st.session_state.user_override:
            st.metric(label="Compliance Score", value="100%")
            st.success("All requirements satisfied.")
        else:
            st.metric(label="Compliance Score", value="50%")
            st.error("Missing requirements detected.")
            
            st.warning("The agent could not find evidence for ISO 27001 certification. Please provide verification.")
            mitigation = st.text_input("Provide ISO 27001 Status:")
            if st.button("Verify & Update Proposal"):
                st.session_state.user_override = True
                st.success("Proposal updated and re-verified by agent! Check the Generated Response tab.")

    with tab4:
        st.markdown("### Final Proposal Draft")
        
        draft = \"\"\"
        **To: Procurement Office**

        We are pleased to submit our proposal.
        
        **1. Vendor Experience**
        Our company was established in 2018, providing us with over 5 years of robust experience in this sector.
        \"\"\"
        
        if st.session_state.user_override:
            draft += \"\"\"
        **2. Security Certifications**
        We confirm that our ISO 27001 certification is currently pending and will be completed by Q4, with all requisite controls already implemented.
        \"\"\"
        else:
            draft += \"\"\"
        **2. Security Certifications**
        *[⚠️ WARNING: Missing ISO 27001 Certification evidence. Action Required]*
        \"\"\"
        
        st.markdown(draft)
        
        if st.session_state.user_override:
            st.download_button(
                label="📄 Generate Final Document (PDF)",
                data="Mock PDF Content",
                file_name="final_proposal.pdf",
                mime="application/pdf"
            )

elif not uploaded_file:
    with tab1:
        st.info("Upload an RFP PDF in the sidebar to begin.")
