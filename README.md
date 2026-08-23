# Student Selector

A lightweight student data pipeline and selection dashboard built with **Python, Pandas, and Streamlit**.

The application allows users to upload a raw student CSV, automatically clean and normalize the data, review the processed records, manage student eligibility, filter candidates by minimum total score, and export the final shortlist as a CSV file.

---

## Features

* Upload raw student CSV files
* Automatic data cleaning and normalization
* Handle inconsistent formats in:

  * Names
  * Gender values
  * Grade values
  * Subject marks
* Validate subject marks
* Recalculate the Total score from Math, Science, and English
* Detect and remove duplicate records
* View cleaned student data
* Search students by name
* Set a minimum Total score requirement
* Mark students as Active or Debarred
* Automatically exclude Debarred students from the shortlist
* View shortlist statistics
* Export the final shortlist as a CSV file

---

## Data Cleaning Pipeline

The application processes the uploaded dataset through several cleaning steps before displaying it.

### Name Normalization

Names are stripped of unnecessary quotation marks and whitespace and converted to a consistent format.

Examples:

```text
MYRA     → Myra
"Myra"   → Myra
'Myra'   → Myra
```

### Gender Normalization

Common textual representations are normalized:

```text
M / m / Male       → Male
F / f / Female     → Female
```

Values whose meaning cannot be reliably determined are not assigned an arbitrary gender.

### Grade Normalization

Numeric values are extracted from inconsistent representations:

```text
Grade 3  → 3
3        → 3
Grade 11 → 11
11       → 11
```

### Marks Normalization

Subject marks are converted into numeric values even when the raw dataset contains text such as:

```text
47 marks → 47
28 marks → 28
43       → 43
```

Marks outside the valid range of 0–100 are excluded.

### Total Validation

The uploaded Total column is not blindly trusted.

The application recalculates Total using:

```text
Total = Math + Science + English
```

This ensures that the shortlist is based on the actual subject marks.

### Duplicate Handling

Duplicate records are removed after normalization to prevent repeated records from affecting the selection process.

---

## Student Selection

After cleaning, users can:

1. Search for a student by name.
2. Set a minimum Total score.
3. Change a student's status between Active and Debarred.
4. View the shortlist in real time.

Only students satisfying both conditions are included:

```text
Status = Active
AND
Total >= Minimum Score
```

Debarring a student immediately removes them from the shortlist without requiring the dataset to be uploaded again.

---

## Shortlist Statistics

The dashboard displays:

* Number of selected students
* Average Total score
* Highest Total score
* Lowest Total score

The final shortlist can be downloaded as a CSV file.

---

## Tech Stack

* **Python**
* **Streamlit**
* **Pandas**

---

## Running Locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd student_selector
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

---

## Project Structure

```text
student_selector/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── .streamlit/
    └── config.toml
```

---

## Demo

A short demonstration of the application is provided below.

**Demo video:** [Watch the demo video](https://drive.google.com/file/d/1zl0cUr-oSHOnU3Jp52I91y9r0tvi7GI4/view?usp=drive_link)

The demonstration covers:

* Uploading the raw dataset
* Automatic data cleaning
* Reviewing the cleaned data
* Applying the minimum Total score filter
* Debarring a student
* Observing the shortlist update in real time
* Downloading the final shortlist

---

## Future Improvements

Potential improvements include:

* More advanced duplicate detection
* Detailed data-quality reports
* Additional filtering options
* Persistent student status storage
* Authentication and role-based access
* Cloud deployment

---