
# average of 100 * # of games posessions for a team in a season
# user has option of choosing the year, and it shows all 32 teams on a
# scatterplot of turnover percentage vs field goal percentage for that year,
# the 2 stats that most accurately show how good a team is

from datetime import date
import requests
import pandas as pd
import json
from tabulate import tabulate  # this is used to print the df in a nice format
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)

app = dash.Dash(__name__)


def get_data(date_user_picked):
    """Takes in a date selected from the Dash calender and retrieves nba game data for that date through an NBA games API.
    Constructs a query string and returns the response that the API returns."""
    url = "https://api-nba-v1.p.rapidapi.com/games"
    querystring = {"date": date_user_picked}
    headers = {
        "X-RapidAPI-Key": "5ac665ada7mshe8f2746ed030651p1ffe7bjsn852a57dc0dcc",
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response


def modify_data(df):
    """this function modifies the df returned by the API response and adds additional data that is needed to make a geoScatter
    plot through Plotly Graph Objects. First, a dictionary is created with all the lat and long coordinates for every major city
    an nba game can be located in. I attempted to use an API to retrieve this data, but I either had to pay money or could not retrieve
    the exact data I wanted. Every city in the dataframe is then decomposed into lat and long coordinates and added to their respective
    lists. For each team, their division in the NBA is determined and added as a new column to the df, which helps split the eventual map
    into 6 distinct colors based on the teams region. A new column was also created to represent the text that would be shown when the user
    hovers their mouse over a bubble. The df is returned with all of these changes."""
    lat_list = []
    long_list = []
    division_list = []
    text_list = []
    coordinate_dictionary = {"Atlanta": [33.7488, -84.3877], "Boston": [42.3601, -71.0589],
                             "Brooklyn": [40.6782, -73.9442],
                             "Charlotte": [35.2271, -80.8431], "Chicago": [41.8781, -87.6298],
                             "Cleveland": [41.4993, -81.6944],
                             "Dallas": [32.7767, -96.7970], "Denver": [39.7392, -104.9903],
                             "Detroit": [42.3314, 83.0458], "San Francisco": [37.7749, -122.4194],
                             "Houston": [29.7604, -95.3698], "Indianapolis": [39.7684, -86.1581],
                             "Los Angeles": [34.0522, -118.2437], "Los Angeles_two": [34.0622, -118.3243],
                             "Memphis": [35.1495, -94.0490], "Miami": [25.7617, -80.1918],
                             "Milwaukee": [43.0389, -87.9065], "Minneapolis": [44.9778, -93.2650],
                             "New Orleans": [29.9511, -90.0715], "New York": [40.7128, 74.0060],
                             "Oklahoma City": [35.4676, -97.5164], "Orlando": [23.5384, -81.3789],
                             "Philadelphia": [39.9526, -75.1652], "Phoenix": [33.4484, -112.0740],
                             "Portland": [45.5152, -122.6784], "Sacramento": [38.5816, -121.4944],
                             "San Antonio": [29.4252, -98.4946], "Toronto": [43.6352, -79.3832],
                             "Salt Lake City": [40.7608, -111.8910], "Washington": [38.9072, -77.0369],
                             "Saitama": [35.8616, -139.6455], "Abu Dhabi": [24.4539, -54.3773],
                             "Paris": [48.8566, -2.3522], "Mexico City": [19.4326, -99.1332]
                             }
    for city in df["arena.city"]:
        if city in coordinate_dictionary.keys():
            lat_list.append(coordinate_dictionary[city][0])
            long_list.append(coordinate_dictionary[city][1])
        else:
            continue
    df["latitude"] = lat_list
    df["longitude"] = long_list

    for team in df['teams.home.nickname']:
        if team in ["Celtics", "76ers", "Knicks", "Nets", "Raptors"]:
            division_list.append("Atlantic")
        elif team in ["Bucks", "Cavaliers", "Bulls", "Pacers", "Pistons"]:
            division_list.append("Central")
        elif team in ["Hawks", "Heat", "Wizards", "Magic", "Hornets"]:
            division_list.append("Southeast")
        elif team in ["Nuggets", "Timberwolves", "Thunder", "Jazz", "Trail Blazers"]:
            division_list.append("Northwest")
        elif team in ["Kings", "Suns", "Clippers", "Warriors", "Lakers"]:
            division_list.append("Pacific")
        else:
            division_list.append("Southwest")

    df["conference"] = division_list
    base_string = "{homeName}:{homePoints} points VS. {visitorsName}:{visitorsPoints} points at {arena}, {city}"
    df['summary'] = [base_string.format(homeName=x, homePoints=y, visitorsName=z, visitorsPoints=a, arena=b, city=c)
                     for x, y, z, a, b, c in
                     zip(df['teams.home.nickname'], df['scores.home.points'], df['teams.visitors.nickname'],
                         df['scores.visitors.points'], df['arena.name'], df['arena.city'])]

    df["total_score"] = df["scores.visitors.points"] + df["scores.home.points"]

    return df


def convert_to_df(response, cols):
    """This function just takes an HTTP response, such as the ones from API calls, and converts that response first
    into a nested JSON file using the Python responses library. Then, that nested JSON is converted to a pandas dataframe
    and many columns from the original df are dropped that are not needed. """
    nba_teams = response.json()  # this is a dict
    df = pd.json_normalize(nba_teams, "response")
    df = df.drop(df.columns[cols], axis=1)
    return df


def set_up_app_layout():
    """This function is what sets up the calender on the webpage and formats the header and graph as well using HTML"""
    app.layout = html.Div([
        html.H3("NBA Data since February 2022", style={"text-align": "left"}),
        dcc.DatePickerSingle(
            id="nba_games_calender",
            min_date_allowed="2022-02-12",
            max_date_allowed="2023-05-19",
            clearable=True,
            reopen_calendar_on_clear=True,
            display_format="YYYY MM DD",
            month_format="MMMM, YYYY",
            initial_visible_month="2023-05-20",
            date=date(2023, 5, 19)
        ),

        html.Div(id="output_container", children=[]),
        html.Br(),

        dcc.Graph(id="nba_map", figure={})

    ])


    @app.callback(
        [Output(component_id='output_container', component_property="children"),
         Output(component_id="nba_map", component_property="figure")],
        [Input(component_id="nba_games_calender", component_property='date')]
    )
    def update_graph(selected_date):
        """This function is what calls the helper functions from above and is what utilizes plotly graph objects to create the
        interactive visualization. """
        container = ""
        response = get_data(selected_date)
        df = convert_to_df(response,
                           [1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 25, 26, 27, 28, 30, 31, 32,
                            33, 34, 35, 38, 39, 40, 41])
        df = modify_data(df)
        fig = go.Figure()

        colors = ["royalblue", "crimson", "lightseagreen", "orange", "lightgrey", "purple"]
        scale = 0.25
        conferences = ["Atlantic", "Central", "Southeast", "Northwest", "Pacific", "Southwest"]
        for i in range(len(conferences)):
            lim = conferences[i]
            df_filtered = df[df['conference'] == lim]
            fig.add_trace(go.Scattergeo(
                locationmode="USA-states",
                lon=df_filtered["longitude"],
                lat=df_filtered["latitude"],
                text=df_filtered["summary"],
                marker=dict(
                    size=df_filtered['total_score' ] /scale,
                    color=colors[i],
                    line_color='rgb(40,40,40)',
                    line_width=0.5,
                    sizemode='area'
                ),
                name='{}'.format(lim[::])
            )
        )

        fig.update_layout(
            title_text='Interactive NBA Map',
            showlegend=True,
            geo=dict(
                scope='usa',
                landcolor='rgb(217, 217, 217)',
            )
        )

        fig.show()

        return container, fig


if __name__ == '__main__':
    set_up_app_layout()
    app.run_server(debug=True)
