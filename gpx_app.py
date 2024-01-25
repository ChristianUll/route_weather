
# -------------------------------------------------------
# loading all the modules

# dealing with gpx files
import gpxpy 
import gpxpy.gpx

#pandas
import pandas as pd

# for calculation of time and distance
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

from datetime import datetime, timedelta



# plotly for easy to use plots
import plotly.express as px
import dash
from dash import Dash, html, dcc, dash_table
import dash_bootstrap_components as dbc

# File handling and requests
import requests # for sending requests in order to receive weather information
import os
# import json
import datetime

# ----------------------------------------------------------------




# -------------------------------------------------------
# Defining the input an variables
# Parsing an existing file:
# -------------------------

gpx_file = open('Basel_Stuttgart.gpx', 'r')
gpx = gpxpy.parse(gpx_file)

# Define the expected avg speed (kmh)
speed_kmh = 30
# ----------------------------------------------------------------




# -----------------------------------------------------------
# Create a dataframe and enrich it with additional information
# Assuming gpx is your parsed gpxpy object with segments
segments_data = []

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            segments_data.append({
                'Latitude': point.latitude,
                'Longitude': point.longitude,
                'Elevation': point.elevation,
                'Time': point.time
            })

# Create DataFrame
df = pd.DataFrame(segments_data)
# ----------------------------------------------------------------



# -------------------------------------------------------------------
# Calclulate elevation, slope, time


# Assuming gpx is your parsed gpxpy object with segments
segments_data = []

previous_point = None
total_distance = 0  # to store the cumulative distance

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            if previous_point is not None:
                # calculate the cumulative distance aka total_distance
                distance_from_previous = geodesic((previous_point.latitude, previous_point.longitude),
                                                  (point.latitude, point.longitude)).meters
                total_distance += distance_from_previous

                #calculate the time to get there
                speed_meters_per_sec = speed_kmh * 1000 / 3600  # convert speed to meters per second
                time_to_reach_point = timedelta(seconds=total_distance / speed_meters_per_sec) if speed_meters_per_sec != 0 else timedelta(seconds=0)

            else:
                time_to_reach_point = timedelta(seconds=0)

                # calclualte the slope
            slope_percent = 0
            if previous_point is not None and (point.longitude != previous_point.longitude or point.latitude != previous_point.latitude):
                # Avoid division by zero
                slope_percent = ((point.elevation - previous_point.elevation) / geodesic((previous_point.latitude, previous_point.longitude),
                                                                                          (point.latitude, point.longitude)).meters) * 100

            segments_data.append({
                'Latitude': point.latitude,
                'Longitude': point.longitude,
                'Elevation': point.elevation,
                'Time': point.time,
                'CumulativeDistance': total_distance,
                'TimeToReach': time_to_reach_point,
                'SlopePercent': slope_percent
            })

            previous_point = point

# Create DataFrame
df = pd.DataFrame(segments_data)

# create some additional track information that can be used to make the track information more colourful
track_name = gpx.tracks[0].name
total_km = int(round((df['CumulativeDistance'].iloc[-1]/1000), 0))
max_height = int(round(df['Elevation'].max(), 0))





# ----------------------------------------------------------------
# Create the plots

# Create a map visualization of the tracks with colour indicator of slope

# define the center of the map
lon_center = df['Longitude'].mean()
lat_center = df['Latitude'].mean()

map_slope = px.scatter_mapbox(df, 
                        lat="Latitude", lon="Longitude", 
                        color="SlopePercent",
                        color_continuous_scale="Viridis",
                        color_continuous_midpoint=0,  # Set the midpoint of the color scale
                        range_color=(-10, 10),  # Set the range of values to be mapped to colors
                        
                        zoom=7, center={'lat': lat_center, 'lon': lon_center}, 
                        mapbox_style='open-street-map'
                                 )

map_slope.update_layout(title_text="Route Map with Slope",
                       plot_bgcolor="#EEEEEE",
                       paper_bgcolor="#DDDDDD")

graph1 = dcc.Graph(figure=map_slope)
# ----------------------------------------------------------------
# create an elevation profile of the track

elevation_profile = px.line(df, x='CumulativeDistance', y='Elevation', height=300, title="Elevation profile", markers=False)
elevation_profile = elevation_profile.update_layout(
        plot_bgcolor="#EEEEEE", paper_bgcolor="#DDDDDD", font_color="black"
    )
graph2 = dcc.Graph(figure=elevation_profile)

# ----------------------------------------------------------------


# ----------------------------------------------------------------
# Build a dash app
app =dash.Dash(external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.layout = html.Div([html.H1('Overview of route', style={'textAlign': 'center', 'color': 'Orange'}),
                       html.H2 (track_name, style={'textAlign': 'center', 'color': 'Orange'}),
                       html.Div(html.P("Using a dash to show information graphs on a loaded gpx file"), 
                                style={'marginLeft': 50, 'marginRight': 25}),
                       html.Div([
                           html.Div([
                                html.Table([
                                    html.Tr([
                                        html.Td(f'Total Distance: {total_km} km'),
                                        html.Td(f'Maximum Height: {max_height} m')
                                    ])
                                ], style={'width': '100%', 'textAlign': 'center'})
                            ]),
                                 graph1, graph2])

                    
])

if __name__ == '__main__':
     app.run_server(port=8097)
# -----------------------------------------------------

