import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

def fetch_data(odata_url, params, username, password):
    session = requests.Session()
    session.auth = (username, password)
    submission_url = f"{odata_url}/Submissions"
    response = session.get(submission_url, params=params)

    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data['value'])
    else:
        st.error(f"Failed to fetch data from {odata_url}")
        return pd.DataFrame()

def preprocess(df):
    df['a01'] = pd.to_datetime(df['a01']).dt.date
    df['SubmitterName'] = df['__system'].apply(lambda x: x.get('submitterName', None)).str.upper()
    df['SubmissionDate'] = df['__system'].apply(lambda x: x.get('SubmissionDate', None))
    df['SubmissionDate'] = pd.to_datetime(df['SubmissionDate']).dt.date
    df['reviewState'] = df['__system'].apply(lambda x: x.get('reviewState', None)).str.upper()
    return df

# Streamlit App Starts
st.header('Enumerator Data Analysis')

# Auth Info
username = 'anupthatal2@gmail.com'
password = 'Super@8848'

params = {
    '$select': 'unique_form_id,a01,b10_dmi,gb12_skip/gc01_skp1/gc20/c20,gb12_skip/gc01_skp1/gc20/c22,__system/submitterName,__system/reviewState,b02,unit_owners,gb12_skip/gc01_skp2/d08'
}

# Primary OData Source (Phase 1)
odata_url_1 = 'https://survey.kuklpid.gov.np/v1/projects/20/forms/kukl_customer_survey_phase1.svc'
df_phase1 = fetch_data(odata_url_1, params, username, password)
df_phase1 = preprocess(df_phase1)
df_phase1['Phase'] = 'Phase 1'

# You can uncomment and add another OData form if needed (e.g., Phase 2)
odata_url_2 = 'https://survey.kuklpid.gov.np/v1/projects/20/forms/kukl_customer_survey_phase2.svc'
df_phase2 = fetch_data(odata_url_2, params, username, password)
df_phase2 = preprocess(df_phase2)
df_phase2['Phase'] = 'Phase 2'

# Combine all data (currently only one loaded)
df = df_phase1  # pd.concat([df_phase1, df_phase2], ignore_index=True)

# Total Review State
total_review_state = df['reviewState'].value_counts(dropna=False).reset_index(name='Count')
total = total_review_state['Count'].sum()
st.subheader(f'Total Data State Counts: {total}')
st.dataframe(total_review_state, width=500)

# Summary
avg = total / df['a01'].nunique()
st.write(f"Total unique collection days: {df['a01'].nunique()}")
st.write(f"Average entries per day: {avg:.2f}")

# Enumerator Summary
enum_info = df.groupby('SubmitterName').agg({'unique_form_id': 'count', 'a01': 'nunique'}).reset_index()
enum_info = enum_info.rename(columns={'unique_form_id': 'Form Collected', 'a01': 'Days Worked'})
enum_info = enum_info.sort_values(by='Form Collected', ascending=False)
enum_info['Days gap'] = df['a01'].nunique() - enum_info['Days Worked']
enum_info['Avg/day (worked)'] = enum_info['Form Collected'] / enum_info['Days Worked']
enum_info['Avg/day (total)'] = enum_info['Form Collected'] / df['a01'].nunique()
st.subheader('Enumerator Summary')
st.dataframe(enum_info, use_container_width=True)

# Enumerator filter
enum_list = df['SubmitterName'].unique().tolist()
enum_selected = st.selectbox('Select Enumerator', enum_list)
df_enum = df[df['SubmitterName'] == enum_selected]

# Individual Enumerator View
st.write(f"Days worked: {df_enum['a01'].nunique()} / {df['a01'].nunique()}")
st.subheader(f'Review States for {enum_selected}')
st.dataframe(df_enum['reviewState'].value_counts(dropna=False))

datewise_report = df_enum.groupby('a01')['reviewState'].value_counts(dropna=False).unstack().fillna(0).reset_index()
st.subheader(f'Daily Review State – {enum_selected}')
st.bar_chart(datewise_report.set_index('a01'))

# All Enumerators bar chart
enum_counts = df.groupby('SubmitterName')['unique_form_id'].count().reset_index()
enum_counts = enum_counts.sort_values(by='unique_form_id', ascending=True)
st.subheader('Form Count per Enumerator')
st.bar_chart(enum_counts.set_index('SubmitterName'))

# Daily Collection Chart
daily_df = df.groupby('a01')['unique_form_id'].count().reset_index()
st.subheader('Total Collection Over Time')
st.line_chart(daily_df.set_index('a01'))

# DMA area filter
num = st.text_input('Days to calculate enum activity by DMA')
if num and num.isdigit():
    num_days = int(num)
    since_date = date.today() - timedelta(days=num_days)
    enum_dma = df[df['a01'] >= since_date]
    dma_stats = enum_dma.groupby(['a01', 'b10_dmi'])['SubmitterName'].unique().reset_index()
    dma_stats['Count'] = enum_dma.groupby(['a01', 'b10_dmi'])['SubmitterName'].count().values
    st.subheader(f'Enumerator-DMA Activity (Last {num_days} days)')
    st.dataframe(dma_stats.sort_values(by='a01', ascending=False), use_container_width=True)
    st.caption(f"Total collected: {dma_stats['Count'].sum()}")
else:
    st.info("Enter number of days to show recent DMA work.")
