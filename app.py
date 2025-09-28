import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Data file paths
DATA_DIR = "data"
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.csv")
PDSA_FILE = os.path.join(DATA_DIR, "pdsa.csv")


def ensure_data_dir():
    """Ensure data directory and default files exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(PROJECTS_FILE):
        example = pd.DataFrame([
            {
                "id": 1,
                "title": "Example Project",
                "smart_aim": "Increase hand hygiene compliance by 10% within 3 months",
                "problem_statement": "Current compliance is at 60%",
                "status": "In Progress",
                "metrics": "Compliance rate",
                "advisor": "Dr. Smith",
                "service": "Infection Control",
                "start_date": "2024-01-01",
                "end_date": "2024-04-01",
                "tags": "hand hygiene",
            }
        ])
        example.to_csv(PROJECTS_FILE, index=False)
    if not os.path.exists(PDSA_FILE):
        pd.DataFrame(
            columns=["project_id", "cycle_name", "plan", "do", "study", "act", "date"]
        ).to_csv(PDSA_FILE, index=False)


def load_data():
    ensure_data_dir()
    projects = pd.read_csv(PROJECTS_FILE)
    pdsa = pd.read_csv(PDSA_FILE)
    return projects, pdsa


def save_data(projects: pd.DataFrame, pdsa: pd.DataFrame):
    projects.to_csv(PROJECTS_FILE, index=False)
    pdsa.to_csv(PDSA_FILE, index=False)


def main():
    st.set_page_config(page_title="Resident QI Project Tracker", layout="wide")
    st.title("Resident QI Project Tracker")

    projects, pdsa = load_data()

    # Sidebar import/export
    st.sidebar.header("Import/Export")
    if st.sidebar.button("Export Projects CSV"):
        st.sidebar.download_button(
            "Download projects.csv",
            projects.to_csv(index=False),
            file_name="projects.csv",
            mime="text/csv",
        )
    if st.sidebar.button("Export PDSA CSV"):
        st.sidebar.download_button(
            "Download pdsa.csv",
            pdsa.to_csv(index=False),
            file_name="pdsa.csv",
            mime="text/csv",
        )

    uploaded_proj = st.sidebar.file_uploader("Import Projects CSV", type=["csv"], key="proj_upload")
    if uploaded_proj is not None:
        projects = pd.read_csv(uploaded_proj)
        save_data(projects, pdsa)
        st.sidebar.success("Projects imported.")

    uploaded_pdsa = st.sidebar.file_uploader("Import PDSA CSV", type=["csv"], key="pdsa_upload")
    if uploaded_pdsa is not None:
        pdsa = pd.read_csv(uploaded_pdsa)
        save_data(projects, pdsa)
        st.sidebar.success("PDSA cycles imported.")

    # Filters
    st.sidebar.header("Filters")
    statuses = ["All"] + sorted(projects["status"].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Status", statuses)

    # Collect tags
    tag_set = set()
    for tag_list in projects["tags"].fillna(""):
        for tag in str(tag_list).split(","):
            tag = tag.strip()
            if tag:
                tag_set.add(tag)
    tags = ["All"] + sorted(tag_set)
    selected_tag = st.sidebar.selectbox("Tag", tags)

    filtered = projects.copy()
    if selected_status != "All":
        filtered = filtered[filtered["status"] == selected_status]
    if selected_tag != "All":
        filtered = filtered[filtered["tags"].str.contains(selected_tag, na=False)]

    st.subheader("Projects")
    selected_index = None
    if not filtered.empty:
        selected_index = st.radio(
            "Select a project:",
            filtered.index,
            format_func=lambda idx: filtered.loc[idx, "title"],
        )
    else:
        st.info("No projects available. Click 'Add new project' to start.")

    if st.button("Add new project"):
        new_id = projects["id"].max() + 1 if not projects.empty else 1
        new_project = pd.DataFrame([
            {
                "id": new_id,
                "title": "",
                "smart_aim": "",
                "problem_statement": "",
                "status": "In Progress",
                "metrics": "",
                "advisor": "",
                "service": "",
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": "",
                "tags": "",
            }
        ])
        projects = pd.concat([projects, new_project], ignore_index=True)
        save_data(projects, pdsa)
        st.experimental_rerun()

    if selected_index is not None and not projects.empty:
        project = projects.loc[selected_index]

        with st.form("project_form"):
            title = st.text_input("Title", value=str(project.get("title", "")))
            smart = st.text_area("SMART Aim", value=str(project.get("smart_aim", "")))
            problem = st.text_area(
                "Problem Statement", value=str(project.get("problem_statement", ""))
            )
            status = st.selectbox(
                "Status",
                ["In Progress", "Completed", "On Hold", "Cancelled"],
                index=["In Progress", "Completed", "On Hold", "Cancelled"].index(project.get("status", "In Progress"))
                if project.get("status", "In Progress") in ["In Progress", "Completed", "On Hold", "Cancelled"]
                else 0,
            )
            metrics = st.text_input("Metrics", value=str(project.get("metrics", "")))
            advisor = st.text_input("Advisor", value=str(project.get("advisor", "")))
            service = st.text_input("Service", value=str(project.get("service", "")))
            start_date = st.date_input(
                "Start Date",
                value=pd.to_datetime(project.get("start_date", datetime.now().date())),
            )
            end_date = st.date_input(
                "End Date",
                value=pd.to_datetime(project.get("end_date", datetime.now().date()))
                if project.get("end_date")
                else datetime.now().date(),
            )
            tags_input = st.text_input("Tags (comma separated)", value=str(project.get("tags", "")))
            if st.form_submit_button("Save Project"):
                projects.loc[selected_index, "title"] = title
                projects.loc[selected_index, "smart_aim"] = smart
                projects.loc[selected_index, "problem_statement"] = problem
                projects.loc[selected_index, "status"] = status
                projects.loc[selected_index, "metrics"] = metrics
                projects.loc[selected_index, "advisor"] = advisor
                projects.loc[selected_index, "service"] = service
                projects.loc[selected_index, "start_date"] = start_date.strftime("%Y-%m-%d")
                projects.loc[selected_index, "end_date"] = end_date.strftime("%Y-%m-%d")
                projects.loc[selected_index, "tags"] = tags_input
                save_data(projects, pdsa)
                st.success("Project saved.")
        if st.button("Delete project"):
            projects = projects.drop(index=selected_index).reset_index(drop=True)
            pdsa = pdsa[pdsa["project_id"] != project["id"]]
            save_data(projects, pdsa)
            st.success("Project deleted.")
            st.experimental_rerun()

        st.subheader("PDSA Cycles")
        project_pdsa = pdsa[pdsa["project_id"] == project["id"]]
        if not project_pdsa.empty:
            edited_pdsa = st.data_editor(project_pdsa, num_rows="dynamic")
            if st.button("Save PDSA cycles"):
                other_pdsa = pdsa[pdsa["project_id"] != project["id"]]
                pdsa = pd.concat([other_pdsa, edited_pdsa], ignore_index=True)
                save_data(projects, pdsa)
                st.success("PDSA cycles saved.")
        else:
            st.info("No PDSA cycles yet.")
        with st.form("pdsa_form"):
            cycle_name = st.text_input("Cycle Name")
            plan = st.text_area("Plan")
            do = st.text_area("Do")
            study = st.text_area("Study")
            act = st.text_area("Act")
            date_cycle = st.date_input("Cycle Date", value=datetime.now().date())
            if st.form_submit_button("Add PDSA"):
                new_pdsa = pd.DataFrame([
                    {
                        "project_id": project["id"],
                        "cycle_name": cycle_name,
                        "plan": plan,
                        "do": do,
                        "study": study,
                        "act": act,
                        "date": date_cycle.strftime("%Y-%m-%d"),
                    }
                ])
                pdsa = pd.concat([pdsa, new_pdsa], ignore_index=True)
                save_data(projects, pdsa)
                st.success("PDSA cycle added.")

    st.sidebar.markdown("### Note")
    st.sidebar.markdown(
        "Data is stored in the local `/data` folder via CSV. Export your data to share or back it up."
    )


if __name__ == "__main__":
    main()
