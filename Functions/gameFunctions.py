import mysql.connector
import pandas as pd
import streamlit as st
import plotly.express as px
#from mysql.connector import Error

import helperFunctions as hf

def get_age_category_filter(age_filter):
    age_conditions = []
    
    if "0-7 (Children)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 0 AND 7")
    if "8-15 (Teens)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 8 AND 15")
    if "16-21 (Young Adults)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 16 AND 21")

    return " OR ".join(age_conditions)

def display_game_data(fetch_function, category, slider_label, default_value, age_filter):
    data, fig = fetch_function(category, default_value, age_filter)

    if not data.empty:
        # Slider for the number of games to display
        top_n = st.slider(
            f"Number of games to display by {slider_label}:",
            min_value=5,
            max_value=20,
            value=5,  
            step=1    
        )

        data, fig = fetch_function(category, top_n, age_filter)
        st.plotly_chart(fig)  
    else:
        st.write("No games found.")

def display_game_datas(fetch_function, category, age_filter):
    data, fig = fetch_function(category, age_filter)

    if not data.empty:
        # Slider for the number of games to display
        data, fig = fetch_function(category, age_filter)
        st.plotly_chart(fig)  
    else:
        st.write("No games found.")

def fetch_games_highest_peak_ccu(selected_category, top_n, age_fil):
    query = f"""
    SELECT 
        g.name, 
        MAX(f.`Peak CCU`) AS highest_peak_ccu
    FROM 
        dim_game g
    JOIN 
        fact_sales f ON g.`AppID` = f.`AppID`
    WHERE 
        FIND_IN_SET('{selected_category}', g.`Categories`) > 0
    """


    if age_fil:
        query += f" AND ({age_fil})"

    query += """
    GROUP BY 
        g.name
    ORDER BY 
        highest_peak_ccu DESC;
    """

    result = hf.execute_query(query)

    # Change to something else (maybe bar graph)
    df = pd.DataFrame(result, columns=['Game Name', 'Highest Peak CCU'])

    df['Highest Peak CCU'] = pd.to_numeric(df['Highest Peak CCU'], errors='coerce')
    highest_ccu = df.nlargest(top_n, 'Highest Peak CCU')
    fig = px.bar(highest_ccu, x='Game Name', y='Highest Peak CCU', title=f'Top {top_n} Games by Highest Peak CCU')

    return highest_ccu, fig

def fetch_games_highest_playtime(selected_category, top_n, age_fil):
    query = f"""
    SELECT 
        g.name, 
        AVG(f.`Average playtime forever`) AS average_playtime, 
        AVG(f.`Median playtime forever`) AS median_playtime
    FROM 
        dim_game g
    JOIN 
        fact_sales f ON g.`AppID` = f.`AppID`
    WHERE 
        FIND_IN_SET('{selected_category}', g.`Categories`) > 0
    """

    if age_fil:
        query += f" AND ({age_fil})"

    query += """
    GROUP BY 
        g.name
    ORDER BY 
        average_playtime DESC;
    """

    result = hf.execute_query(query)

    # Convert the result to a DataFrame for display in Streamlit
    df = pd.DataFrame(result, columns=['Game Name', 'Average Playtime', 'Median Playtime'])

    df['Average Playtime'] = pd.to_numeric(df['Average Playtime'], errors='coerce')
    df['Median Playtime'] = pd.to_numeric(df['Median Playtime'], errors='coerce')

    #Drop null values
    df = df.dropna(subset=['Average Playtime', 'Median Playtime'])

    highest_ave_playtime = df.nlargest(top_n, 'Average Playtime')

    long_df = highest_ave_playtime.melt(id_vars='Game Name', 
                                                value_vars=['Average Playtime', 'Median Playtime'],
                                                var_name='Playtime Type', 
                                                value_name='Playtime')

    fig = px.bar(
        long_df, 
        x='Game Name', 
        y='Playtime', 
        color='Playtime Type',
        title=f'Top {top_n} Games by Average and Median Playtime',
        barmode='group'
    )

    return highest_ave_playtime, fig

def fetch_games_required_age(selected_category, age_fil, top_n=5):
    query = f"""
    SELECT 
        `Required Age`, 
        COUNT(`Required Age`) AS total_count
    FROM dim_game
    WHERE
        FIND_IN_SET('{selected_category}', `categories`) > 0
    """

    if age_fil:
        query += f" AND ({age_fil})"

    query += """
    GROUP BY 
        `Required Age`
    ORDER BY 
        total_count DESC;
    """

    result = hf.execute_query(query)
    df = pd.DataFrame(result, columns=['required_age', 'total_count'])
    df['total_count'] = pd.to_numeric(df['total_count'], errors='coerce')
    required_age_count = df.nlargest(top_n, 'total_count')

    fig = px.bar(
        required_age_count, 
        x='required_age', 
        y='total_count', 
        title=f'Count of Games Grouped by Age Requirement',
        labels={'required_age': 'Required Age', 'total_count': 'Game Count'},
        text='total_count',  
        color='required_age', 
        barmode='group',  
    )

    fig.update_layout(
        xaxis=dict(
            tickmode='linear',  
            dtick=1  
        ),
        xaxis_title='Required Age',
        yaxis_title='Game Count',
        xaxis_tickangle=0,  
        template='plotly_white',  
    )

    return required_age_count, fig

