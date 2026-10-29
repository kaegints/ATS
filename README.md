# RoleFit Auditor (v1.0)

A Streamlit application that can run locally or on a cloud server that compares a resume against a job posting with a transparent evidence-led scoring rubric. Supports text-based PDF, DOCX and TXT documents, plus pasted text. The app runs in a browser and disables Streamlit usage telemetry where supported. It is not a universal employer ATS simulator.

## Getting started

1. **Install Python 3.10+** from https://www.python.org/downloads/ if necessary.
2. Unzip the folder.
3. **Mac:** Open Terminal in the folder and run `bash start_mac.command`. **Windows:** Double-click `start_windows.bat`. The first run installs dependencies from PyPI.
4. A local browser window opens (normally http://localhost:8501). Close the terminal to stop the application.

Alternatively, run:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The included `.streamlit/config.toml` limits individual uploads to 20 MB and disables usage telemetry where supported. It does not force a localhost bind, so the same files can run on Streamlit Community Cloud.

A fictional posting and resume (`sample_job.txt`, `sample_resume.txt`) are included for a trial run.

## Workflow

1. Upload a job advertisement and a resume, or paste either document as text.
2. Read the **proposed requirements list** carefully. Exclude promotional text or irrelevant criteria, split multi-part requirements into separate rows, and reclassify must-haves vs nice-to-haves. Add any missed qualifications.
3. Inspect the deterministic 0–100 **documented role-fit** score. Default section weights: Required **55**, Preferred **20**, Responsibilities **25**. Within sections, requirements have equal weight unless you change Importance. If a category is absent, remaining weights are proportionally adjusted. Some conditions (years, visas, work authorization, clearance) require manual review and are excluded rather than guessed.
4. Expand individual requirements to see the supporting resume excerpts or gaps. **Balanced** gives partial credit to close textual overlap and conservative synonyms; **Strict** uses tougher rules.
5. Inspect the resume extraction/readability score **separately**. This is a diagnostic, not proof the document will parse in a particular employer's ATS.
6. Export the detailed CSV and full JSON audit.

## Scope and validity

The word "objective" here means the **same input, criterion set, and settings produce the same result**. It does not mean that the score is externally validated. Actual applicant tracking systems are not a single universal model, and organizations often configure their own matching criteria. This tool does *not* estimate the odds of an interview or imply a real ATS threshold.

The weights (55/20/25), textual matching cutoffs, importance scores and document diagnostics are transparent **design choices, not scientifically validated coefficients**. If you change the job requirement list, you are changing the evaluation rubric. The tool has not been benchmarked against labeled hiring decisions. It does not assess the truth or depth of a claimed skill.

No LLM is used, so the app does not invent experience or send your documents to an outside API. The skill synonym dictionary is conservative and visible in `engine.py`. Results can still include false positives and false negatives. Review before making changes. Only describe skills and experience you can substantiate.

## Evidence informing design

The literature and primary ATS vendor documentation support the use of transparent job-related criteria, extraction quality checks, and human review. They **do not** verify the precise numeric scoring weights:

- Raghavan, M., Barocas, S., Kleinberg, J., & Levy, K. (2020). *Mitigating Bias in Algorithmic Hiring: Evaluating Claims and Practices*. ACM FAT*, 469–481. https://doi.org/10.1145/3351095.3372828
- Köchling, A., & Wehner, M. C. (2020). *Discriminated by an algorithm: A systematic review...*. *Business Research, 13*, 795–848. https://doi.org/10.1007/s40685-020-00134-w
- *Job description parsing with explainable transformer based ensemble models to extract the technical and non-technical skills* (2024). *Natural Language Processing Journal, 9*, 100102. https://doi.org/10.1016/j.nlp.2024.100102
- Greenhouse, *Talent Matching – Data Processing FAQ*: https://support.greenhouse.io/hc/en-us/articles/41131616864283-Talent-Matching-Data-Processing-FAQ
- Concordia University, *Applicant Tracking Systems (ATS) and your job search*: https://www.concordia.ca/students/success/career-planning/job-search/understanding-applicant-tracking-systems-ats.html

## Known limitations

- Scanned/image-only PDFs will not extract without separate OCR. Export a text-based PDF, upload the original DOCX, or paste text.
- Older `.doc` files need conversion to `.docx` first.
- Word text boxes and PDF multi-column reading order can be unreliable. The app provides the extracted text for inspection.
- Auto-extracted job criteria may be incomplete, contain non-criteria, or combine multiple concepts.
- Generic vocabulary can earn partial credit without proving ability. Exact keyword matches also need human scrutiny.
- User-defined category weights and requirement list are heuristics, and there are no empirical score cutoffs for interview likelihood.
- Data is processed on the host computer or server in Streamlit sessions. A cloud deployment sends uploaded documents to the hosting provider. Use a private deployment for personal resumes, and avoid confidential materials unless you accept the provider’s data practices.

## Development / tests

Run `python -m pytest -q` from this directory after installing `pytest`. The app uses no network API after dependency installation.


## GitHub + Streamlit Community Cloud (no local Python required)

1. Create a new repository on https://github.com/new (prefer **Private**).
2. Upload the **contents of this unzipped folder** into the repository root, not the ZIP file. Make sure `app.py`, `engine.py`, `requirements.txt`, and `.streamlit/config.toml` appear as source files. You may omit sample text, tests, and start scripts.
3. Open https://share.streamlit.io, sign in with GitHub and select **Create app** > **Yup, I have an app**.
4. Select your repository, branch `main`, and entrypoint `app.py`. Deploy. The service installs dependencies from `requirements.txt`.
5. Use the generated `*.streamlit.app` URL to access the interface. For a private repository, check that the deployed app is **private** before uploading your resume.

**Important:** GitHub stores code, not uploaded resumes from the running app. In a cloud deployment the resume and posting are transmitted to Streamlit's server for processing; this is not the same privacy model as running entirely on your computer. Never commit real resumes or other private documents to the repository itself. Community Cloud is subject to its availability and plan limitations.

## GitHub Codespaces (alternative)

Open your GitHub repository, select **Code > Codespaces > Create codespace on main**, and in the terminal run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 0.0.0.0
```

Open the forwarded port 8501 in your browser. Codespaces is intended for development/testing, not a permanently hosted site. Keep forwarded port visibility **Private** for personal documents.
