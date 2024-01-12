import requests
import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit_folium
import matplotlib.pyplot as plt
import plotly
import plotly.express as px
import folium
from streamlit_folium import folium_static

st.set_page_config(layout='wide', page_title='Test Dashboard')

def read_file(file):
    if file is not None:
        if file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            # Excel file
            df = pd.read_excel(file)
        elif file.type == 'text/csv':
            # CSV file
            df = pd.read_csv(file)
        else:
            st.error("Invalid file format. Please upload a CSV or Excel file.")
            return None
        return df
    return None

# function to extract info from api

def bulk_pc_lookup(postcodes):
    # set up the api request
    url = "https://api.postcodes.io/postcodes"
    headers = {"Content-Type": "application/json"}
    
    # divide postcodes into batches of 100
    postcode_batches = [postcodes[i:i + 100] for i in range(0, len(postcodes), 100)]
    
    # to store the results
    postcode_data = []
    
    for batch in postcode_batches:
        # specify our input data and response, specifying that we are working with data in json format
        data = {"postcodes": batch}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # check for successful response
        if response.status_code == 200:
            results = response.json()["result"]
            
            for result in results:
                postcode = result["query"]
                
                if result["result"] is not None:
                    lsoa = result["result"]["codes"]["lsoa"]
                    latitude = result["result"]["latitude"]
                    longitude = result["result"]["longitude"]
                    region = result["result"]["region"]
                    postcode_data.append({"Charity Postcode": postcode, "Latitude": latitude, "Longitude": longitude, "LSOA Code": lsoa, "Region": region})
        else:
            # handle errors for each batch
            print(f"Error in batch: {response.status_code}")
    
    return postcode_data

def main():

    imd = pd.read_csv('imd condensed.csv')
    rurb = pd.read_csv('rural urban.csv')

    secret_key = st.text_input("Enter the password: ")

    if secret_key == 'TURBINE':

        st.title("Test App")
        
        uploaded_file = st.file_uploader(
            "Upload your CSV or Excel file containing postcodes. Please make sure your postcode column is called 'Postcode'",
            type=["csv", "xlsx"]
        )

        if uploaded_file is not None:
            st.markdown('### See analysis:')
            
            df = read_file(uploaded_file)
            
            if df is not None:
                # Continue with your analysis using the uploaded DataFrame (df)
                st.write(df.head())

            #st.write(df.head())

            postcodes = df['Postcode'].tolist()

            output = bulk_pc_lookup(postcodes)

            output_df = pd.DataFrame(output)

            total_matches = output_df.shape[0]

            total_postcodes = df.shape[0]
            
            st.write(f"Matches found for {total_matches} out of {total_postcodes} postcodes")
            #st.write(output_df)

            imd_df = pd.merge(output_df, imd, left_on='LSOA Code', right_on='lsoa code (2011)', how='left')
            rurb_df = pd.merge(output_df, rurb, left_on='LSOA Code', right_on='lsoa code (2011)', how='left')

            #st.write(imd_df)
            #st.write(rurb_df)

            regions = ['All'] + list(imd_df['Region'].unique())
            selected_region = st.selectbox('Filter by Region', regions)

            if selected_region == 'All':
                filter_imd_df = imd_df
            else:
                filter_imd_df = imd_df[imd_df['Region'] == selected_region]

            total_rows = len(filter_imd_df)
            imd_123 = len(filter_imd_df[filter_imd_df['IMD dec'].isin([1, 2, 3])])
            percentage_in_lowest = round((imd_123 / total_rows) * 100)

            imd_8910 = len(filter_imd_df[filter_imd_df['IMD dec'].isin([8, 9, 10])])
            percentage_in_highest = round((imd_8910 / total_rows) * 100)

            plot_df = filter_imd_df.groupby('IMD dec').size().reset_index(name='Count')

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label='Average IMD', value = round(imd_df['IMD dec'].mean()))
            with col2:
                st.metric(label='Percentage of Postcodes in IMD 1 to 3', value=percentage_in_lowest)
            with col3:
                st.metric(label='Percentage of Postcodes in IMD 8 to 10', value=percentage_in_highest)

            #st.write(plot_df)

            fig1, fig2 = st.columns(2)

            with fig1:
                fig1 = px.bar(plot_df, x='IMD dec', y='Count', title='IMD Bar Chart')
                st.write(fig1)
            with fig2:
                mean_lat = output_df['Latitude'].mean()
                mean_lon = output_df['Longitude'].mean()

                m = folium.Map(location=[mean_lat, mean_lon], zoom_start=6)

                for idx, row in filter_imd_df.iterrows():
                    postcode = row['Charity Postcode']
                    lat = row['Latitude']
                    lon = row['Longitude']
                    marker_text = f"Postcode: {postcode}"

                    folium.Marker(
                        location=[lat, lon],
                        popup=marker_text,
                        icon=folium.Icon(color='blue')
                    ).add_to(m)

                folium_static(m)


if __name__ == '__main__':
    main()