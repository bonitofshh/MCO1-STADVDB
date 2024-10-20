# MySQL connection setup
import mysql.connector
import pandas as pd
import plotly.express as px
from mysql.connector import Error

def create_connection():
    return mysql.connector.connect(
        host="localhost",   
        port=3306,                    
        user="root",             
        password="123456",     
        database="mco1"     
    )

def get_age_category_filter(age_filter):
    age_conditions = []
    
    if "0-7 (Children)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 0 AND 7")
    if "8-15 (Teens)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 8 AND 15")
    if "16-21 (Young Adults)" in age_filter:
        age_conditions.append("`Required Age` BETWEEN 16 AND 21")

    return " OR ".join(age_conditions)

def fetch_games_highest_peak_ccu(included_categories, excluded_categories, top_n, age_fil):
    include_query = " OR ".join([f"g.categories LIKE '%{category}%'" for category in included_categories])
    exclude_query = " AND ".join([f"g.categories NOT LIKE '%{category}%'" for category in excluded_categories])

    query = f"""
    SELECT 
        g.name, 
        MAX(f.`Peak CCU`) AS highest_peak_ccu
    FROM 
        dim_game g
    JOIN 
        fact_sales f ON g.`AppID` = f.`AppID`
    WHERE 
        ({include_query})
    """

    if exclude_query:
        query += f" AND ({exclude_query})"

    if age_fil:
        query += f" AND ({age_fil})"

    query += """
    GROUP BY 
        g.name
    ORDER BY 
        highest_peak_ccu DESC;
    """

    #Execute query
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()

    # Change to something else (maybe bar graph)
    df = pd.DataFrame(result, columns=['Game Name', 'Highest Peak CCU'])

    df['Highest Peak CCU'] = pd.to_numeric(df['Highest Peak CCU'], errors='coerce')

    highest_ccu = df.nlargest(top_n, 'Highest Peak CCU')

    fig = px.bar(highest_ccu, x='Game Name', y='Highest Peak CCU', title=f'Top {top_n} Games by Highest Peak CCU')

    return highest_ccu, fig

def fetch_games_highest_playtime(included_categories, excluded_categories, top_n, age_fil):
    include_query = " OR ".join([f"g.categories LIKE '%{category}%'" for category in included_categories])
    exclude_query = " AND ".join([f"g.categories NOT LIKE '%{category}%'" for category in excluded_categories])

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
        ({include_query})
    """

    if exclude_query:
        query += f" AND ({exclude_query})"

    if age_fil:
        query += f" AND ({age_fil})"

    query += """
    GROUP BY 
        g.name
    ORDER BY 
        average_playtime DESC;
    """

    # Execute query
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()

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