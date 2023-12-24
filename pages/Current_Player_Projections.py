import os
import streamlit as st
from streamlit_extras.app_logo import add_logo
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
from google.cloud import bigquery
import db_dtypes

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/api_keys/pristine-nebula-408601-132510f1855a.json'

#api key instead:
secrets = st.secrets["gcp_service_account"]

st.set_page_config(layout="wide")

# Use the app_logo function to display the logo
add_logo("pictures/DarkoLogo.png", height=185)

# Current Player Skill Projections
st.header("Version: 2023-11-24")
link_text = "Support DARKO"
link_url = "https://www.buymeacoffee.com/darko"

# Create a subheader with the updated link
st.subheader(f"[{link_text}]({link_url})")
st.markdown("DARKO by: @kmedved, V1 Application by @anpatt7, V2 by @roy.krishnan")


searchable_columns = ['Player', 'Team', 'Experience']
col1, col2 = st.columns(2)
with col1:
    selected_column = st.selectbox('Column to search in:', searchable_columns)
with col2:
    search_query = st.text_input('Text to Search:')

@st.cache_data(ttl=600)
def run_query(query):
    # Initialize a BigQuery Client
    client = bigquery.Client()
    # Execute the query
    query_job = client.query(query)
    # Wait for the job to complete and return the result as a DataFrame
    return query_job.result().to_dataframe()

# Define your SQL query to select all data from the table
player_talent_query = """
    SELECT * 
    FROM `pristine-nebula-408601.DARKO.DARKO_full_set`
"""

# Run the query and store the result in a DataFrame
df = run_query(player_talent_query)

#LOCAL DATA FILE: 
#df = pd.read_csv("data/DARKO_player_talent_2023-11-24.csv")

datetime = dt.datetime.now()
datetime = datetime.strftime("%Y-%m-%d_%H-%M-%S")
st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"DARKO_{datetime}.csv",
        mime="text/csv"
    )

if search_query != '': 
    df_display = df.drop("nba_id", axis=1)
    filtered_df = df_display[df_display[selected_column].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = df.drop("nba_id", axis=1)

# Ensure 'DPM Improvement' column exists in filtered_df
# Function to highlight values in different percentiles of the 'DPM Improvement' column
def highlight_by_percentile(s):
    # Filter out NaN values and calculate percentiles on the remaining data
    non_nan_values = s.dropna()
    percentile_25 = np.percentile(non_nan_values, 25)
    percentile_50 = np.percentile(non_nan_values, 50)
    percentile_75 = np.percentile(non_nan_values, 75)

    # Apply styles based on percentile ranges and handle NaN values
    return ['background-color: yellow' if pd.isna(v) else
            'background-color: red' if v <= percentile_25 else
            'background-color: orange' if percentile_25 < v <= percentile_50 else
            'background-color: green' if percentile_50 < v <= percentile_75 else
            'background-color: lightgreen' for v in s]

filtered_df['DPM_Improvement'] = pd.to_numeric(filtered_df['DPM_Improvement'], errors='coerce')
# Ensure 'DPM Improvement' column exists in filtered_df
if 'DPM_Improvement' in filtered_df.columns:
    # Apply the highlighting function to the 'DPM Improvement' column of filtered_df
    styled_df = filtered_df.style.apply(highlight_by_percentile, subset=['DPM_Improvement'])
    # Display the styled DataFrame in Streamlit
    st.dataframe(styled_df, hide_index= True)
else:
    st.write("Column 'DPM Improvement' not found in the DataFrame.")

st.write('**Select Player or Search by Player Name**')

def search_players():
    active_player_query = """
    SELECT * 
    FROM `pristine-nebula-408601.DARKO.active_players`"""
    df_filtered = run_query(active_player_query)
    
    #LOCAL STORAGE
    #df_filtered = pd.read_csv("data/active_player_charts.csv")

    left_column, middle_column, right_column = st.columns(3)
    player_names = df_filtered['player_name'].unique()

    if 'selected_player' not in st.session_state:
        st.session_state.selected_player = None

    # Streamlit UI for selecting a player
    left_column, middle_column, right_column = st.columns(3)
    player_names = df_filtered['player_name'].unique()

    # Text input for searching by player name
    with middle_column:
        text_search = st.text_input("Search by Player Name")

    # Determine the index of the player in the dropdown if found in the text search
    player_index = 0
    if text_search in player_names:
        player_index = list(player_names).index(text_search)

    # Select box for choosing the player
    with left_column:
        selected_player = st.selectbox('Select Player', player_names, index=player_index)

    # Filter the DataFrame for the selected player
    player_data = df_filtered[df_filtered['player_name'] == selected_player]

    with right_column:
        df_filtered['dpm'] = pd.to_numeric(df_filtered['dpm'], errors='coerce')
        df_filtered['o_dpm'] = pd.to_numeric(df_filtered['o_dpm'], errors='coerce')
        df_filtered['d-dpm'] = pd.to_numeric(df_filtered['d_dpm'], errors='coerce')
        df_filtered['tr_fg3_pct'] = pd.to_numeric(df_filtered['tr_fg3_pct'], errors='coerce')
        df_filtered['tr_ft_pct'] = pd.to_numeric(df_filtered['tr_fg3_pct'], errors='coerce')
        df_filtered['tr_ft_ar'] = pd.to_numeric(df_filtered['tr_ft_ar'], errors='coerce')
        df_filtered['tr_rim_fga_100'] = pd.to_numeric(df_filtered['tr_rim_fga_100'], errors='coerce')

        talent_options = {
            'DPM': 'dpm',
            'O-DPM': 'o_dpm',
            'D-DPM': 'd_dpm',
            'FG3%': 'tr_fg3_pct',
            'FG3A Rate %': 'tr_fg3_ar',
            'FT%': 'tr_ft_pct',
            'FTA Rate %': 'tr_ft_ar',
            'Rim FGA/100': 'tr_rim_fga_100'
        }
        talent_display_name = st.selectbox("Select Talent Metric: ", list(talent_options.keys()))

    # Grouping the data by season and calculating the average DPM for each season
    talent_column_name = talent_options[talent_display_name]

    # Sorting the data by season for the line that goes through points
    df_filtered['season'] = pd.to_numeric(df_filtered['season'], errors='coerce')
    seasonal_dpm_sorted = player_data.sort_values('season')

    # Setting up the linear regression model
    model = LinearRegression()
    model.fit(seasonal_dpm_sorted['season'].values.reshape(-1, 1), seasonal_dpm_sorted[talent_column_name].values)
    seasonal_dpm_sorted['predicted_dpm'] = model.predict(seasonal_dpm_sorted['season'].values.reshape(-1, 1))

    # Group the data by season
    grouped = player_data.groupby('season')

    # Initialize an empty DataFrame to store the adjusted data
    adjusted_data = pd.DataFrame()

    # Iterate over each season group
    for season, group in grouped:
        # Create an offset for each point within the season
        offsets = np.linspace(-0.3, 0.3, len(group))
        group['adjusted_season'] = group['season'] + offsets
        adjusted_data = pd.concat([adjusted_data, group])

    # Define the current point size and increase it for larger markers
    current_point_size = plt.rcParams['lines.markersize'] ** 2
    larger_point_size = 2.5 * current_point_size

    #creating average line of fit: 
    seasonal_average = player_data.groupby('season')[talent_column_name].mean().reset_index()

    #Creating graph limiters
    min_year = seasonal_dpm_sorted['season'].min()
    max_year = seasonal_dpm_sorted['season'].max()
    plt.xlim(min_year, max_year)

    # Creating the plot
    plt.figure(figsize=(18, 6))
    plt.scatter(adjusted_data['adjusted_season'], adjusted_data[talent_column_name], s=larger_point_size, color='blue', alpha=0.5,edgecolors= 'white', label=f'Values of {talent_display_name}')
    plt.plot(seasonal_average['season'], seasonal_average[talent_column_name], color='black', linewidth=2, label='Seasonal Average')
    plt.plot(seasonal_dpm_sorted['season'], seasonal_dpm_sorted['predicted_dpm'], color='red', linewidth=2, label='Best Fit Line')
    plt.xticks(adjusted_data['season'].unique().astype(int))
    plt.xlabel('Season')
    plt.ylabel(talent_display_name)
    plt.title(f'{selected_player} {talent_display_name} Over Seasons')
    plt.legend()

    # Displaying the plot in Streamlit
    st.pyplot(plt)

    with open("dummy.pdf", "rb") as pdf_file:
        PDFbyte = pdf_file.read()

    st.download_button(label="Export_Report",
                    data=PDFbyte,
                    file_name="test.pdf",
                    mime='application/octet-stream')
search_players()