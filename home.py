import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

def data_collection():
    odata_url = 'https://survey.kuklpid.gov.np/v1/projects/16/forms/kukl_customer_survey_01.svc'
    params = {
        '$select': 'unique_form_id,a01,b10_sub_dmi,gb12_skip/gc01_skp1/gc20/c20,gb12_skip/gc01_skp1/gc20/c22,__system/submitterName,__system/reviewState,b02,unit_owners,gb12_skip/gc01_skp2/d08'
    }
    submission_entity_set = 'Submissions'
    username = 'anupthatal2@gmail.com'
    password = 'Super@8848'

    session = requests.Session()
    session.auth = (username, password)

    submission_url = f"{odata_url}/{submission_entity_set}"
    response = session.get(submission_url, params=params)

    data = response.json()

    final_df = pd.DataFrame(data['value'])

    final_df['a01'] = pd.to_datetime(final_df['a01']).dt.date
    final_df['SubmitterName'] = final_df['__system'].apply(lambda x: x.get('submitterName', None)).str.upper()
    final_df['reviewState'] = final_df['__system'].apply(lambda x: x.get('reviewState', None)).str.upper()

    return final_df

df = data_collection()

# Header
st.header('Enum Analysis')

# Total Review State Counts
total_review_state = df['reviewState'].value_counts(dropna=False)
st.subheader('Total Review State Counts')
st.dataframe(total_review_state, width=500)
total=total_review_state['Count'].sum()
st.subheader(f'Total data State Counts: {total}')

# Enumerator Information
enum_list = df['SubmitterName'].unique().tolist()
enum_selected = st.selectbox('Select Enumerator', enum_list)
df_enum = df[df['SubmitterName'] == enum_selected]

# Enumerator Statistics
unique_dates_count = len(df_enum['a01'].unique())
st.write(f"Number of days worked for {enum_selected}: {unique_dates_count}")
st.write(f"Total days in the dataset: {len(df['a01'].unique())}")

# Review State Counts for Selected Enumerator
enum_report = df_enum['reviewState'].value_counts(dropna=False)
st.subheader(f'Review State Counts for {enum_selected}')
st.dataframe(enum_report, use_container_width=True, height=160)

# Date-wise Review State Counts for Selected Enumerator
datewise_report = df_enum.groupby('a01')['reviewState'].value_counts().unstack(fill_value=0)
st.subheader(f'Date-wise Review State Counts for {enum_selected}')
st.bar_chart(datewise_report, use_container_width=True, height=300)

# Bar Chart for Enumerators and Form Counts
grouped_df = df.groupby('SubmitterName')['unique_form_id'].count().reset_index()
sorted_df = grouped_df.sort_values(by='unique_form_id',ascending=True)
st.subheader('Enumerator-wise Form Counts')
st.bar_chart(sorted_df.set_index('SubmitterName'))

today_date = date.today()
yesterday_date = today_date - timedelta(days=1)
st.write("Yesterday's Date:", yesterday_date)
df_date=df[df['a01']==yesterday_date]
pivot_table = pd.pivot_table(df_date, values='a01', index='SubmitterName', aggfunc='count')
st.bar_chart(pivot_table)


total_collection_date = df.groupby('a01')['unique_form_id'].count().reset_index()
st.subheader('Total Collection Date Counts')
st.line_chart(total_collection_date, x='a01', y='unique_form_id')
