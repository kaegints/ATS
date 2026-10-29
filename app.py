"""Launch locally: streamlit run app.py"""
import csv
from io import BytesIO, StringIO
import hashlib
import html
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from engine import (
    CATEGORY_WEIGHTS, extract_document, parsing_diagnostic,
    extract_requirements, evaluate, recommendations, VERSION,
)

st.set_page_config(page_title='RoleFit Auditor', page_icon='▦', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
    .block-container{padding-top:2rem;max-width:1190px;padding-bottom:3rem}
    h1,h2,h3{letter-spacing:-.035em}
    h1{font-size:2.4rem!important}
    .subtitle{color:#67717e;font-size:1.04rem;margin-top:-.5rem;margin-bottom:1.2rem}
    .eyebrow{font-size:.76rem;letter-spacing:.12em;text-transform:uppercase;color:#687586;font-weight:700}
    .note{background:#f6f7fa;border:1px solid #e3e7ed;border-radius:10px;padding:12px 16px;color:#475467;font-size:.9rem}
    [data-testid="stMetric"]{border:1px solid #dfe5ec;background:#fafbfc;padding:18px;border-radius:12px}
    [data-testid="stMetricLabel"]{color:#667085}
    [data-testid="stMetricValue"]{letter-spacing:-.04em}
    div.stButton>button[kind="primary"]{background:#162a42;border-color:#162a42}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">Evidence-led · Document analysis · v1.0</div>', unsafe_allow_html=True)
st.title('RoleFit Auditor')
st.markdown('<p class="subtitle">Compare a resume against a job posting using a transparent, reviewable scoring rubric.</p>', unsafe_allow_html=True)
st.info('This is an independent **resume-to-job fit assessment**, not an employer ATS score or interview probability. The weights and match thresholds are openly documented heuristics, not empirically calibrated hiring predictions.')

with st.expander('How the assessment works', expanded=False):
    st.markdown('''**1. Extract:** Read selectable text from PDF, DOCX, TXT or Markdown documents. Scanned PDFs are flagged and not OCR-converted.\n\n**2. Review requirements:** Proposed job requirements are automatically classified as Required, Preferred or Responsibilities. Review and edit these before trusting the result.\n\n**3. Match:** Each requirement is compared with resume passages using conservative phrase/term matching and a limited, published synonym list. We give credit for the **best supporting passage**, not for repeated keywords.\n\n**4. Calculate:** Required = **55%**, Preferred = **20%**, Responsibilities = **25%**. Within each category, each requirement has an adjustable importance weight (default 1). Categories with no automatically assessable requirements are excluded and the remaining weights are proportionally re-normalized. Requirements needing manual verification are excluded from the denominator.\n\n**5. Review evidence:** Examine the resume excerpts, gaps and parsing diagnostics. No evidence is fabricated and the tool does not verify the truth of resume statements.\n\n**Balanced** permits high overlap or named-term evidence. **Strict** requires closer textual agreement. Both are deterministic, without any third-party API.''')

st.subheader('1. Add your documents')
col_job, col_resume = st.columns(2, gap='large')
with col_job:
    st.markdown('**Job posting**')
    job_file = st.file_uploader('Upload job posting (PDF, DOCX, TXT)', type=['pdf', 'docx', 'txt', 'md'], key='job')
    job_paste = st.text_area('Or paste the posting text', height=125, placeholder='Paste the complete job posting here...')
with col_resume:
    st.markdown('**Resume**')
    resume_file = st.file_uploader('Upload resume (PDF, DOCX, TXT)', type=['pdf', 'docx', 'txt', 'md'], key='resume')
    resume_paste = st.text_area('Or paste the resume text', height=125, placeholder='Paste resume text here if you prefer...')

def read_input(uploaded, pasted, label):
    if uploaded:
        payload = uploaded.getvalue()
        try:
            return extract_document(payload, uploaded.name)
        except Exception as exc:
            st.error(f'{label}: {exc}')
            return None
    if pasted.strip():
        return extract_document(pasted.encode('utf-8'), f'{label}.txt')
    return None

job = read_input(job_file, job_paste, 'job_posting')
resume = read_input(resume_file, resume_paste, 'resume')

if not job or not resume:
    st.markdown('---')
    st.caption('Files are processed on the computer or server hosting the app. On Streamlit Community Cloud, uploads are transferred to that service, not stored in your GitHub repository by this application.')
    st.stop()

if job.stats['word_count'] < 35 or resume.stats['word_count'] < 35:
    st.error('Not enough text was extracted to run a meaningful assessment. For a scanned PDF, obtain a text-based version or paste the contents directly.')
    with st.expander('Extracted text diagnostics'):
        st.write('Job:', job.stats, job.issues)
        st.write('Resume:', resume.stats, resume.issues)
    st.stop()

# Uploaded content / pasted content changes refresh automatically generated criteria.
job_hash = hashlib.sha256(job.text.encode('utf-8')).hexdigest()
if st.session_state.get('current_job_hash') != job_hash:
    detected = extract_requirements(job.text)
    st.session_state['requirements'] = pd.DataFrame([
        {'Include': True, 'Requirement': c.requirement, 'Category': c.category, 'Importance': 1.0}
        for c in detected
    ], columns=['Include', 'Requirement', 'Category', 'Importance'])
    st.session_state['current_job_hash'] = job_hash

st.markdown('---')
st.subheader('2. Verify the evaluation criteria')
st.caption('The detector can misclassify or merge requirements. Edit, delete, add and reclassify rows. A reviewed list is necessary for a meaningful score.')
if len(st.session_state['requirements']) == 0:
    st.warning('No requirements were detected. Add criteria manually in the editor below.')

edited = st.data_editor(
    st.session_state['requirements'], hide_index=True, num_rows='dynamic', use_container_width=True,
    column_config={
        'Include': st.column_config.CheckboxColumn('Include', default=True),
        'Requirement': st.column_config.TextColumn('Requirement from job posting', required=True, width='large'),
        'Category': st.column_config.SelectboxColumn('Category', options=list(CATEGORY_WEIGHTS), required=True),
        'Importance': st.column_config.NumberColumn('Importance', min_value=.5, max_value=5., step=.5, default=1., help='Within-category multiplier; defaults to 1.'),
    }, key=f'requirements_editor_{job_hash[:12]}',
)

strict = st.toggle('Strict matching (less credit for paraphrases)', value=False)
st.caption('Review the list above before interpreting the score. Direct phrase matches are strongest; partial matches only indicate potentially relevant wording.')

criteria = []
for _, row in edited.fillna({'Importance': 1.0, 'Include': False, 'Category': 'Required', 'Requirement': ''}).iterrows():
    criteria.append({'include': bool(row['Include']), 'requirement': str(row['Requirement']),
                     'category': str(row['Category']), 'importance': float(row['Importance'])})
if not any(c['include'] and len(c['requirement']) >= 3 for c in criteria):
    st.warning('Add at least one included requirement to generate an assessment.')
    st.stop()

assessment = evaluate(criteria, resume.text, strict)
other_assessment = evaluate(criteria, resume.text, not strict)
parse_score, parse_issues = parsing_diagnostic(resume)

st.markdown('---')
st.subheader('3. Assessment')

left, mid, right = st.columns([1, 1, 1])
with left:
    st.metric('Documented role fit', f"{assessment['score']}/100" if assessment['score'] is not None else 'N/A')
with mid:
    st.metric('Automatically assessed', str(assessment['assessed']))
with right:
    st.metric('Needs manual verification', str(assessment['manual']))
if assessment['score'] is None:
    st.warning('No criteria can be automatically assessed. Please review the eligibility/experience requirements manually and add assessable criteria.')
else:
    st.progress(assessment['score'] / 100)
    balanced_score = assessment['score'] if not strict else other_assessment['score']
    strict_score = assessment['score'] if strict else other_assessment['score']
    st.caption(f'Sensitivity check: Balanced {balanced_score}/100 · Strict {strict_score}/100. The difference reflects the importance of matching assumptions, not a statistical confidence interval.')
    if assessment['assessed'] < 5:
        st.warning('Fewer than five criteria were assessed. The overall score may be unstable; inspect the full posting and add missing criteria.')
    if assessment['manual']:
        st.warning(f"{assessment['manual']} requirement(s) are excluded from the score because the resume alone cannot confirm them. The reported score describes assessed criteria only.")

section_data = []
for name in CATEGORY_WEIGHTS:
    item = assessment['sections'][name]
    section_data.append({'Dimension': name, 'Score': f"{item['score']:.1f}/100" if item['score'] is not None else 'Not assessable',
                         'Rubric weight': f"{item['weight']:.0f}%", 'Assessed items': item['assessed'],
                         'Manual review': item['manual']})
st.dataframe(pd.DataFrame(section_data), use_container_width=True, hide_index=True)
st.markdown('**Evidence by requirement**')
results = assessment['results']
if results:
    counts = pd.Series([r['status'] for r in results]).value_counts()
    st.caption(' · '.join(f'{label}: {count}' for label, count in counts.items()))
    filter_status = st.multiselect('Filter evidence', options=sorted(set(r['status'] for r in results)), default=[])
    shown = [r for r in results if not filter_status or r['status'] in filter_status]
    for idx, item in enumerate(shown, 1):
        score_label = 'Manual' if item['credit'] is None else f"{item['credit'] * 100:.0f}% textual credit"
        with st.expander(f"{item['category']} · {item['status']} ({score_label}) — {item['requirement'][:110]}"):
            st.markdown(f"**Job criterion:** {html.escape(item['requirement'])}")
            st.write(item['reason'])
            if item['evidence']:
                st.markdown('**Closest resume evidence (verbatim)**')
                st.markdown('> ' + html.escape(item['evidence']).replace('\n', '\n> '))
                if item['terms']:
                    st.caption('Recognized common terms: ' + ', '.join(item['terms']))
            elif item['credit'] == 0:
                st.write('No sufficiently specific evidence detected in the resume.')

st.markdown('**Highest-priority content gaps**')
recs = recommendations(assessment)
if recs:
    for n, rec in enumerate(recs, 1):
        st.markdown(f"{n}. **{rec['requirement']}** ({rec['category']}). {rec['advice']}")
else:
    st.write('No unmet automatically assessed criteria detected under the selected matching mode. This does not establish real-world qualification or eligibility.')

st.markdown('---')
st.subheader('4. Document parsing diagnostic')
st.caption('This is a basic text-extraction check, not a measured compatibility score for an employer ATS.')
st.metric('Text-readability check', f'{parse_score}/100')
st.write(f"Extracted **{resume.stats['word_count']:,} words** from **{resume.filename}**.")
if parse_issues:
    for issue in parse_issues:
        st.warning(issue)
else:
    st.success('No obvious issues found by the text extractor. Review the reading order below to check for problems this test may miss.')
with st.expander('Inspect extracted resume reading order'):
    st.code(resume.text[:24000], language=None)
with st.expander('Inspect extracted job posting'):
    st.code(job.text[:30000], language=None)

st.markdown('---')
st.subheader('5. Export your assessment')

meta = {
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'app_version': VERSION, 'job_filename': job.filename, 'resume_filename': resume.filename,
    'rubric_weights': CATEGORY_WEIGHTS, 'parsing_diagnostic': parse_score,
    'parsing_issues': parse_issues, 'assessment': assessment,
    'note': 'Heuristic textual alignment, not a proprietary ATS result or hiring probability.'
}

entries = pd.DataFrame([{
    'Category': r['category'], 'Requirement': r['requirement'],
    'Importance': r['importance'], 'Status': r['status'],
    'Textual credit': r['credit'], 'Resume evidence': r['evidence'],
    'Rationale': r['reason'],
} for r in results])

c1, c2 = st.columns(2)
with c1:
    st.download_button('Download detailed CSV', data=entries.to_csv(index=False).encode('utf-8-sig'),
                       file_name='rolefit_requirements.csv', mime='text/csv', use_container_width=True)
with c2:
    st.download_button('Download full JSON audit', data=json.dumps(meta, indent=2, ensure_ascii=False),
                       file_name='rolefit_audit.json', mime='application/json', use_container_width=True)

st.caption('Privacy: the app makes no model/API calls and does not intentionally save uploads or results to a database. Files are processed on the host. When deployed to Streamlit Community Cloud, uploads are sent to that service and may be accessible to the service operator. Use a private app and avoid confidential documents unless its privacy terms meet your needs.')
with st.expander('Methodology, evidence and limitations'):
    st.markdown('''**Sources informing the design (not validation of the numerical weights):**

- Raghavan, M., Barocas, S., Kleinberg, J., & Levy, K. (2020). *Mitigating bias in algorithmic hiring: Evaluating claims and practices*. ACM FAT*. [DOI](https://doi.org/10.1145/3351095.3372828).
- Köchling, A., & Wehner, M. C. (2020). *Discriminated by an algorithm: A systematic review of discrimination and fairness by algorithmic decision-making in the context of HR recruitment and HR development*. Business Research, 13, 795–848. [DOI](https://doi.org/10.1007/s40685-020-00134-w).
- *Job description parsing with explainable transformer based ensemble models to extract the technical and non-technical skills* (2024). Natural Language Processing Journal, 9, 100102. [DOI](https://doi.org/10.1016/j.nlp.2024.100102).
- [Greenhouse Talent Matching – Data Processing FAQ](https://support.greenhouse.io/hc/en-us/articles/41131616864283-Talent-Matching-Data-Processing-FAQ) (shows employer-specific calibration, skill evidence and human review).
- [Concordia University career guidance on ATS](https://www.concordia.ca/students/success/career-planning/job-search/understanding-applicant-tracking-systems-ats.html) (document formatting and keywords).

**Limits:** This is not a reverse-engineered employer ATS and has not been calibrated against recruiter outcomes, job-performance data or known thresholds. Similar wording is not proof of skill. Job-ad requirement extraction can omit, over-include or misclassify items; inspect the list. Strict matching can miss legitimate paraphrases; balanced matching can falsely credit generic terms. Multiple items inside one bullet may need to be split manually. Experience duration, right-to-work and location must be checked manually. Reading-order checks here do not represent all ATS parsers. No demographic profiling or protected-characteristic scoring is used.''')
