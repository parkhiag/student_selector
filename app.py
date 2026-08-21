import re
import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Student Selector",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown("""
<style>

    /* Main app */
    .stApp {
        background-color: #f7f8fa;
    }

    /* Remove Streamlit top padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Header */
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #111827;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Status badge */
    .status-ready {
        background: #ecfdf3;
        color: #027a48;
        padding: 7px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Cards */
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        height: 120px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #111827;
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* Section headings */
    .section-title {
        font-size: 1.15rem;
        font-weight: 650;
        color: #111827;
        margin-top: 1.5rem;
        margin-bottom: 0.2rem;
    }

    .section-description {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }

    /* Upload box */
    [data-testid="stFileUploader"] {
        background: white;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 10px;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
    }

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# DATA CLEANING FUNCTIONS
# ---------------------------------------------------------

def clean_name(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    # Remove surrounding quotes/apostrophes
    value = value.strip("\"'")

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    # Consistent capitalization
    return value.title()


def clean_gender(value):
    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value in ["m", "male"]:
        return "Male"

    if value in ["f", "female"]:
        return "Female"

    return None


def clean_grade(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    match = re.search(r"\d+", value)

    if match:
        return int(match.group())

    return None


def clean_marks(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    match = re.search(r"\d+", value)

    if match:
        return int(match.group())

    return None


def clean_data(df):

    df = df.copy()

    # Normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # Rename possible variations
    column_mapping = {
        "name": "Name",
        "gender": "Gender",
        "grade": "Grade",
        "math": "Math",
        "maths": "Math",
        "science": "Science",
        "english": "English",
        "total": "Total"
    }

    df = df.rename(columns=column_mapping)

    required_columns = [
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {', '.join(missing_columns)}"
        )

    # Clean individual columns
    df["Name"] = df["Name"].apply(clean_name)
    df["Gender"] = df["Gender"].apply(clean_gender)
    df["Grade"] = df["Grade"].apply(clean_grade)

    for column in ["Math", "Science", "English"]:
        df[column] = df[column].apply(clean_marks)

    # Remove rows where essential marks are missing
    df = df.dropna(
        subset=["Math", "Science", "English"]
    )

    # Convert marks to integers
    for column in ["Math", "Science", "English"]:
        df[column] = df[column].astype(int)

    # Validate marks
    df = df[
        (df["Math"].between(0, 100)) &
        (df["Science"].between(0, 100)) &
        (df["English"].between(0, 100))
    ]

    # Recalculate Total
    df["Total"] = (
        df["Math"] +
        df["Science"] +
        df["English"]
    )

    # Remove exact duplicate records
    df = df.drop_duplicates()

    # Add status
    df["Status"] = "Active"

    return df.reset_index(drop=True)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    st.markdown(
        '<div class="app-title">Student Selector</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="app-subtitle">'
        'Clean, evaluate and shortlist students from your dataset.'
        '</div>',
        unsafe_allow_html=True
    )

with header_col2:
    st.markdown(
        '<div style="text-align:right; margin-top:10px;">'
        '<span class="status-ready">● System Ready</span>'
        '</div>',
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Upload Dataset</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Upload the raw student CSV. The data will be cleaned automatically.'
    '</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose CSV file",
    type=["csv"],
    label_visibility="collapsed"
)


# ---------------------------------------------------------
# PROCESS DATA
# ---------------------------------------------------------

if uploaded_file is not None:

    try:

        raw_df = pd.read_csv(uploaded_file)

        df = clean_data(raw_df)

        st.session_state["student_data"] = df

        st.success(
            f"Successfully processed {len(df)} students."
        )

    except Exception as e:

        st.error(f"Unable to process dataset: {e}")


# ---------------------------------------------------------
# INTERACTIVE STUDENT MANAGEMENT
# ---------------------------------------------------------

if "student_data" in st.session_state:

    df = st.session_state["student_data"].copy()

    # -----------------------------------------------------
    # FILTER CONTROLS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Student Selection</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Search students, set the minimum score and manage eligibility.'
        '</div>',
        unsafe_allow_html=True
    )

    filter_col1, filter_col2 = st.columns([2, 1])

    with filter_col1:

        search_query = st.text_input(
            "Search student",
            placeholder="Search by name...",
            label_visibility="visible"
        )

    with filter_col2:

        minimum_score = st.number_input(
            "Minimum Total Score",
            min_value=0,
            max_value=300,
            value=150,
            step=1
        )

    # -----------------------------------------------------
    # STUDENT STATUS MANAGEMENT
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Student Status</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Toggle students between Active and Debarred. '
        'Debarred students are automatically excluded from the shortlist.'
        '</div>',
        unsafe_allow_html=True
    )

    # Header
    header_cols = st.columns([2.5, 1.2, 0.8, 0.8, 1, 1, 1, 1.2])

    headers = [
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
        "Total",
        "Status"
    ]

    for col, header in zip(header_cols, headers):
        with col:
            st.markdown(
                f"**{header}**"
            )

    st.divider()

    # -----------------------------------------------------
    # DISPLAY STUDENTS
    # -----------------------------------------------------

    for index in df.index:

        row = df.loc[index]

        # Search filtering
        if search_query:
            if search_query.lower() not in row["Name"].lower():
                continue

        cols = st.columns(
            [2.5, 1.2, 0.8, 0.8, 1, 1, 1, 1.2]
        )

        with cols[0]:
            st.write(row["Name"])

        with cols[1]:
            st.write(row["Gender"] if row["Gender"] else "—")

        with cols[2]:
            st.write(row["Grade"] if pd.notna(row["Grade"]) else "—")

        with cols[3]:
            st.write(row["Math"])

        with cols[4]:
            st.write(row["Science"])

        with cols[5]:
            st.write(row["English"])

        with cols[6]:
            st.write(row["Total"])

        with cols[7]:

            is_debarred = row["Status"] == "Debarred"

            new_status = st.toggle(
                "Debar",
                value=is_debarred,
                key=f"status_{index}",
                label_visibility="collapsed"
            )

            df.loc[index, "Status"] = (
                "Debarred" if new_status else "Active"
            )

    # Save updated statuses
    st.session_state["student_data"] = df

    # -----------------------------------------------------
    # SHORTLIST
    # -----------------------------------------------------

    shortlist = df[
        (df["Status"] == "Active") &
        (df["Total"] >= minimum_score)
    ].copy()

    # Apply search to shortlist too
    if search_query:
        shortlist = shortlist[
            shortlist["Name"]
            .str.lower()
            .str.contains(
                search_query.lower(),
                na=False
            )
        ]

    st.markdown(
        '<div class="section-title">Shortlist</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Students meeting the minimum score and active status criteria.'
        '</div>',
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # SHORTLIST STATISTICS
    # -----------------------------------------------------

    selected_count = len(shortlist)

    if selected_count > 0:

        average_score = shortlist["Total"].mean()
        highest_score = shortlist["Total"].max()
        lowest_score = shortlist["Total"].min()

    else:

        average_score = 0
        highest_score = 0
        lowest_score = 0

    stat1, stat2, stat3, stat4 = st.columns(4)

    with stat1:
        st.metric(
            "Selected Students",
            selected_count
        )

    with stat2:
        st.metric(
            "Average Total",
            f"{average_score:.1f}"
        )

    with stat3:
        st.metric(
            "Highest Total",
            highest_score
        )

    with stat4:
        st.metric(
            "Lowest Total",
            lowest_score
        )

    # -----------------------------------------------------
    # SHORTLIST TABLE
    # -----------------------------------------------------

    if selected_count > 0:

        st.dataframe(
            shortlist[
                [
                    "Name",
                    "Gender",
                    "Grade",
                    "Math",
                    "Science",
                    "English",
                    "Total"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------------------------
        # EXPORT
        # -------------------------------------------------

        csv = shortlist.to_csv(index=False)

        st.download_button(
            label="Download Shortlist CSV",
            data=csv,
            file_name="student_shortlist.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "No students currently meet the selection criteria."
        )

        
    # -----------------------------------------------------
    # CLEANED DATA
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Cleaned Student Data</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Review the normalized student records below.'
        '</div>',
        unsafe_allow_html=True
    )

    display_columns = [
        "Name",
        "Gender",
        "Grade",
        "Math",
        "Science",
        "English",
        "Total",
        "Status"
    ]

    st.dataframe(
        df[display_columns],
        use_container_width=True,
        hide_index=True
    )