import io
import re

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Student Selector",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    .stApp {
        background-color: #f7f8fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

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

    .status-ready {
        background: #ecfdf3;
        color: #027a48;
        padding: 7px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

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

    [data-testid="stFileUploader"] {
        background: white;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 10px;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# VECTORIZED DATA CLEANING HELPERS
#
# These replace the old row-by-row .apply(...) calls with
# pandas vectorized string/regex operations. For a 5,000+
# row dataset this is meaningfully faster because pandas
# processes the whole column in one pass instead of calling
# a Python function once per row.
# =========================================================

def clean_name_column(series: pd.Series) -> pd.Series:
    """Trim, strip stray quotes, collapse whitespace, title-case."""

    is_missing = series.isna()

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.strip("\"'")
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    cleaned[is_missing] = None
    cleaned = cleaned.replace("", None)

    return cleaned


def clean_gender_column(series: pd.Series) -> pd.Series:
    """
    Map common gender spellings to Male / Female.
    Anything ambiguous (blank, '0', '1', typos, etc.) is left
    as missing rather than guessed at, matching the original
    intent of the app.
    """

    mapping = {
        "m": "Male",
        "male": "Male",
        "f": "Female",
        "female": "Female",
    }

    return series.astype(str).str.strip().str.lower().map(mapping)


def extract_first_number(series: pd.Series) -> pd.Series:
    """Pull the first integer out of a messy text/number column."""

    extracted = series.astype(str).str.extract(r"(\d+)", expand=False)
    return pd.to_numeric(extracted, errors="coerce")


@st.cache_data(show_spinner=False)
def clean_data(raw_bytes: bytes) -> pd.DataFrame:
    """
    Full cleaning pipeline. Cached on the raw file bytes so the
    (relatively expensive) cleaning pass for a large file only
    ever runs once per unique upload, no matter how many times
    the app reruns afterwards.
    """

    df = pd.read_csv(io.BytesIO(raw_bytes))

    # -----------------------------------------------------
    # Normalize column names
    # -----------------------------------------------------

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

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

    required_columns = ["Name", "Gender", "Grade", "Math", "Science", "English"]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    # -----------------------------------------------------
    # Clean columns (vectorized)
    # -----------------------------------------------------

    df["Name"] = clean_name_column(df["Name"])
    df["Gender"] = clean_gender_column(df["Gender"])
    df["Grade"] = extract_first_number(df["Grade"])

    for column in ["Math", "Science", "English"]:
        df[column] = extract_first_number(df[column])

    # -----------------------------------------------------
    # Remove rows with missing essential marks
    # -----------------------------------------------------

    df = df.dropna(subset=["Math", "Science", "English"])

    # -----------------------------------------------------
    # Convert marks to integers
    # -----------------------------------------------------

    for column in ["Math", "Science", "English"]:
        df[column] = df[column].astype(int)

    # -----------------------------------------------------
    # Validate marks (0-100 range)
    # -----------------------------------------------------

    df = df[
        df["Math"].between(0, 100)
        & df["Science"].between(0, 100)
        & df["English"].between(0, 100)
    ]

    # -----------------------------------------------------
    # Recalculate Total
    # -----------------------------------------------------

    df["Total"] = df["Math"] + df["Science"] + df["English"]

    # -----------------------------------------------------
    # Remove exact duplicates
    # -----------------------------------------------------

    df = df.drop_duplicates()

    # -----------------------------------------------------
    # Add status
    # -----------------------------------------------------

    df["Status"] = "Active"

    df = df.reset_index(drop=True)

    # -----------------------------------------------------
    # 1-based row numbering (instead of pandas' default 0-based)
    # -----------------------------------------------------

    df.index = pd.RangeIndex(start=1, stop=len(df) + 1)
    df.index.name = "S.No."

    return df


# =========================================================
# HEADER
# =========================================================

header_col1, header_col2 = st.columns([5, 1])

with header_col1:

    st.markdown('<div class="app-title">Student Selector</div>', unsafe_allow_html=True)

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


# =========================================================
# UPLOAD DATASET
# =========================================================

st.markdown('<div class="section-title">Upload Dataset</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="section-description">'
    'Upload the raw student CSV. The data will be cleaned automatically. '
    'Handles large files (5,000+ students) smoothly.'
    '</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose CSV file",
    type=["csv"],
    label_visibility="collapsed"
)


# =========================================================
# PROCESS DATA
# =========================================================

if uploaded_file is not None:

    file_id = (uploaded_file.name, uploaded_file.size)

    if st.session_state.get("uploaded_file_id") != file_id:

        try:

            with st.spinner("Cleaning and validating student records..."):
                df = clean_data(uploaded_file.getvalue())

            if df.empty:
                st.error(
                    "No valid student records remained after cleaning. "
                    "Please check the source file."
                )

            else:
                st.session_state["student_data"] = df
                st.session_state["uploaded_file_id"] = file_id

                # Reset the status editor's widget state for the new dataset
                st.session_state.pop("student_status_editor", None)

                st.success(f"Successfully processed {len(df)} students.")

        except Exception as e:

            st.error(f"Unable to process dataset: {e}")


# =========================================================
# MAIN APPLICATION
# =========================================================

if "student_data" in st.session_state:

    df = st.session_state["student_data"]

    # -----------------------------------------------------
    # Section switcher.
    #
    # NOTE: we deliberately use st.radio (bound to
    # st.session_state via `key`) instead of st.tabs here.
    # st.tabs has no session_state binding — its selected
    # tab is tracked purely on the frontend — and on the
    # very first interaction with a widget nested inside a
    # tab (e.g. the first Debar checkbox click), Streamlit's
    # component tree briefly re-syncs and the tab snaps back
    # to index 0. A state-backed radio doesn't have that
    # failure mode: the current section is real Streamlit
    # state, so it survives every rerun, including the first
    # edit.
    # -----------------------------------------------------

    section_options = ["📋 Cleaned Data", "✅ Manage Status", "🏆 Shortlist"]

    if "active_section" not in st.session_state:
        st.session_state["active_section"] = section_options[0]

    st.radio(
        "Section",
        section_options,
        horizontal=True,
        key="active_section",
        label_visibility="collapsed"
    )

    active_section = st.session_state["active_section"]

    # =====================================================
    # STEP 1 — CLEANED DATA
    # =====================================================

    if active_section == "📋 Cleaned Data":

        st.markdown('<div class="section-title">Cleaned Student Data</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="section-description">'
            f'{len(df)} normalized student records. Use the search icon in the '
            'table toolbar (top-right of the table) to quickly find a student.'
            '</div>',
            unsafe_allow_html=True
        )

        cleaned_columns = ["Name", "Gender", "Grade", "Math", "Science", "English", "Total", "Status"]

        st.dataframe(
            df[cleaned_columns],
            use_container_width=True,
            height=500,
            hide_index=False
        )

        cleaned_csv = df[cleaned_columns].to_csv().encode("utf-8")

        st.download_button(
            label="Download Cleaned Data CSV",
            data=cleaned_csv,
            file_name="cleaned_students.csv",
            mime="text/csv"
        )

    # =====================================================
    # STEP 2 — MANAGE STATUS (DEBAR)
    # =====================================================

    elif active_section == "✅ Manage Status":

        st.markdown('<div class="section-title">Student Status</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="section-description">'
            'Check the Debar box to exclude a student from the shortlist. '
            'Use the search icon in the table toolbar to find a student.'
            '</div>',
            unsafe_allow_html=True
        )

        # -------------------------------------------------
        # Build the editable table. We intentionally show the
        # FULL dataset here (rather than a search-filtered
        # subset) and rely on the data editor's own built-in
        # search/sort toolbar. Streamlit's data_editor tracks
        # edits by row position, so re-filtering the underlying
        # rows on every keystroke (as the previous version did
        # by rebuilding the widget key per search string) both
        # risks edits landing on the wrong row and leaves a
        # growing pile of stale widget state in memory. Keeping
        # one stable widget over the full dataset avoids both.
        # -------------------------------------------------

        status_display = df[["Name", "Gender", "Grade", "Math", "Science", "English", "Total"]].copy()
        status_display["Debar"] = df["Status"] == "Debarred"

        editor_key = f"student_status_editor_{st.session_state['uploaded_file_id']}"

        edited_status = st.data_editor(
            status_display,
            use_container_width=True,
            height=550,
            hide_index=False,

            disabled=["Name", "Gender", "Grade", "Math", "Science", "English", "Total"],

            column_config={
                "Name": st.column_config.TextColumn("Name"),
                "Gender": st.column_config.TextColumn("Gender"),
                "Grade": st.column_config.NumberColumn("Grade"),
                "Math": st.column_config.NumberColumn("Math"),
                "Science": st.column_config.NumberColumn("Science"),
                "English": st.column_config.NumberColumn("English"),
                "Total": st.column_config.NumberColumn("Total"),
                "Debar": st.column_config.CheckboxColumn(
                    "Debar",
                    help="Check this box to debar the student",
                    default=False
                )
            },

            key=editor_key
        )

        # -------------------------------------------------
        # Update statuses in one vectorized pass instead of
        # looping row-by-row in Python — much faster at scale.
        # -------------------------------------------------

        df["Status"] = np.where(edited_status["Debar"], "Debarred", "Active")

        st.session_state["student_data"] = df

        debarred_count = int((df["Status"] == "Debarred").sum())

        st.caption(f"{debarred_count} student(s) currently debarred.")

    # =====================================================
    # STEP 3 — SHORTLIST
    # =====================================================

    else:

        st.markdown('<div class="section-title">Shortlist</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="section-description">'
            'Students meeting the minimum score and active status criteria.'
            '</div>',
            unsafe_allow_html=True
        )

        filter_col1, filter_col2 = st.columns([2, 1])

        with filter_col1:
            search_query = st.text_input("Search student", placeholder="Search by name...")

        with filter_col2:
            minimum_score = st.number_input(
                "Minimum Total Score",
                min_value=0,
                max_value=300,
                value=150,
                step=1
            )

        shortlist = df[(df["Status"] == "Active") & (df["Total"] >= minimum_score)]

        if search_query:
            shortlist = shortlist[
                shortlist["Name"].str.lower().str.contains(search_query.lower(), na=False)
            ]

        # -------------------------------------------------
        # Stats
        # -------------------------------------------------

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
            st.metric("Selected Students", selected_count)

        with stat2:
            st.metric("Average Total", f"{average_score:.1f}")

        with stat3:
            st.metric("Highest Total", highest_score)

        with stat4:
            st.metric("Lowest Total", lowest_score)

        # -------------------------------------------------
        # Table + export
        # -------------------------------------------------

        if selected_count > 0:

            shortlist_columns = ["Name", "Gender", "Grade", "Math", "Science", "English", "Total"]

            st.dataframe(
                shortlist[shortlist_columns],
                use_container_width=True,
                height=450,
                hide_index=False
            )

            shortlist_csv = shortlist[shortlist_columns].to_csv().encode("utf-8")

            st.download_button(
                label="Download Shortlist CSV",
                data=shortlist_csv,
                file_name="student_shortlist.csv",
                mime="text/csv"
            )

        else:
            st.info("No students currently meet the selection criteria.")