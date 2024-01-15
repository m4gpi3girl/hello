# import packages
# ------------------------------------------------------------------
# for making api request
import requests
# for api data
import json

# obv pandas
import pandas as pd
# always import this never use it but its habit at this point
import numpy as np

# for streamlit
import streamlit as st
# for folium maps in streamlit
import streamlit_folium
# to keep the map on the page 
from streamlit_folium import folium_static

# folium for maps
import folium

# data viz
import matplotlib.pyplot as plt
# data viz
import plotly
# data viz
import plotly.express as px

# for reading excel
import openpyxl
# ------------------------------------------------------------------




# set page configuration
# ------------------------------------------------------------------
st.set_page_config(layout='wide', page_title='Test Dashboard')
# -------------------------------------------------------------------


# a function to read the user imported file and read it into pandas df
# --------------------------------------------------------------------
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
# ---------------------------------------------------------------------



# function to extract lat, lon and other geographic info from api
# -----------------------------------------------------------------
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
                    postcode_data.append({"Charity Postcode": postcode, 
                                          "Latitude": latitude, 
                                          "Longitude": longitude, 
                                          "LSOA Code": lsoa, 
                                          "Region": region})
        else:
            # handle errors for each batch
            print(f"Error in batch: {response.status_code}")
    
    return postcode_data
# --------------------------------------------------------------------------------


# main stramlit app - all code
# -----------------------------------------------------------------------------------
def main():

    # read imd and rural urban info
    # --------------------------------------------
    # imd
    imd = pd.read_csv('imd condensed.csv')
    # rural urban
    rurb = pd.read_csv('rural urban.csv')
    # merged
    geo_df = pd.merge(rurb, imd, on='lsoa code (2011)')
    # --------------------------------------------------





    # enter secret key to proceed with app
    # --------------------------------------------------
    secret_key = st.text_input("Enter the password: ")

    if secret_key == 'TURBINE':

        # app title
        st.title("Test App")
        
        # user can upload file
        uploaded_file = st.file_uploader(
            "Upload your CSV or Excel file containing postcodes. Please make sure your postcode column is called 'Postcode'",
            type=["csv", "xlsx"]
        )

        # to do if the file is accepted
        if uploaded_file is not None:
            
            # read user input data
            df = read_file(uploaded_file)
            
            #if df is not None:
                # Continue with your analysis using the uploaded DataFrame (df)
                #st.write(df.head())
            #st.write(df.head())

            # read postcode column as a list
            postcodes = df['Postcode'].tolist()

            # run postcodes through the api function
            output = bulk_pc_lookup(postcodes)

            # convert to pandas df
            output_df = pd.DataFrame(output)

            # count number of matches
            total_matches = output_df.shape[0]

            # number of postcodes in user uploaded data
            total_postcodes = df.shape[0]
            
            # text showing how many matches found
            st.write(f"Matches found for {total_matches} out of {total_postcodes} postcodes")
            
            # if wanting to see ones that didnt match-------------------------------------------------
            if st.button('See rows with no match'):
                df1 = df
                df2 = output_df
                df2 = df2.rename(columns={'Charity Postcode':'Postcode'})
                # Merge the dataframes based on the specified columns
                merged_df = pd.merge(df1, df2, on='Postcode', how='left', indicator=True)
                # Create a third dataframe containing rows from df1 not present in df2
                not_in_df2 = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)
                st.write(not_in_df2)
            # -----------------------------------------------------------------------------------------------


            #st.write(output_df)
            # merge all data ---------------------------------------------------------------------------------
            imd_df = pd.merge(output_df, imd, left_on='LSOA Code', right_on='lsoa code (2011)', how='left')
            rurb_df = pd.merge(output_df, rurb, left_on='LSOA Code', right_on='lsoa code (2011)', how='left')
            geo_df = pd.merge(imd_df, rurb_df, on='Charity Postcode', how='left')
            # clean data
            geo_df = geo_df.drop(columns=['lsoa code (2011)_y', 'lsoa code (2011)_x', 'lsoa code (2021)_y', 'lsoa code (2021)_x', 'Latitude_y', 'Longitude_y', 'LSOA Code_x', 'LSOA Code_y', 'Region_y'])
            # rename
            geo_df = geo_df.rename(columns={
                'Charity Postcode': 'Postcode',
                'Latitude_x':'lat',
                'Longitude_x':'lon',
                'Region_x':'Region'
            })
            # ------------------------------------------------------------------------

            # check cols
            st.write(geo_df.head())
            
            # organising filters ---------------------------------------------------------
            regions = ['All'] + list(geo_df['Region'].unique())
            selected_region = st.selectbox('Filter by Region', regions)

            if selected_region == 'All':
                filter_df = geo_df
            else:
                filter_df = geo_df[geo_df['Region'] == selected_region]
            # -----------------------------------------------------------------------------

            # calculating metric values based on filters ----------------------------------
            total_rows = len(filter_df)
            imd_123 = len(filter_df[filter_df['IMD dec'].isin([1, 2, 3])])
            percentage_in_lowest = round((imd_123 / total_rows) * 100)

            imd_8910 = len(filter_df[filter_df['IMD dec'].isin([8, 9, 10])])
            percentage_in_highest = round((imd_8910 / total_rows) * 100)

            plot_df = filter_df.groupby('IMD dec').size().reset_index(name='Count')
            # ------------------------------------------------------------------------------

            # displaying metrics -----------------------------------------------------------
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label='Total Postcodes', value=filter_df['Postcode'].nunique())
            with col2:
                st.metric(label='Average IMD', value = round(filter_df['IMD dec'].mean()))
            with col3:
                st.metric(label='Percentage of Postcodes in IMD 1 to 3', value=percentage_in_lowest)
            with col4:
                st.metric(label='Percentage of Postcodes in IMD 8 to 10', value=percentage_in_highest)
            # -----------------------------------------------------------------------------------------
                
            # visuals ---------------------------------------------------------------------------------
            fig1, fig2 = st.columns(2)

            with fig1:
                fig1 = px.bar(plot_df, x='IMD dec', y='Count', title='IMD Bar Chart')
                st.write(fig1)
            with fig2:
                mean_lat = output_df['Latitude'].mean()
                mean_lon = output_df['Longitude'].mean()

                m = folium.Map(location=[mean_lat, mean_lon], zoom_start=6)

                for idx, row in filter_df.iterrows():
                    postcode = row['Postcode']
                    lat = row['lat']
                    lon = row['lon']
                    marker_text = f"Postcode: {postcode}"

                    folium.Marker(
                        location=[lat, lon],
                        popup=marker_text,
                        icon=folium.Icon(color='blue')
                    ).add_to(m)

                folium_static(m)
            # --------------------------------------------------------------------------

            # download info --------------------------------------------------------------
            st.subheader('Thank you for using this prototype app. If you would like to download the data, please see below!')

            if st.button("Download IMD Data as CSV"):
                csv_file = imd_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data = csv_file,
                    file_name="IMD Postcode Data.csv",
                    mime="text/csv"
                )
            
            if st.button("Download Rural/Urban Data as CSV"):
                csv_file = rurb_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_file,
                    file_name="Rural Urban Postcode Data",
                    mime="text/csv"
                )
            # -------------------------------------------------------------------------------------

# -----------------------------------------------
if __name__ == '__main__':
    main()
# -----------------------------------------------