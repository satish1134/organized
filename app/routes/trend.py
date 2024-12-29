import os
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State
from datetime import datetime, time
from flask import Blueprint, render_template, current_app

bp = Blueprint('trend', __name__)

@bp.route('/trend-analysis', endpoint='trend')
def trend():
    try:
        current_app.logger.info('Rendering trend.html...')
        return render_template('trend.html')
    except Exception as e:
        current_app.logger.error(f"Error loading trend analysis: {str(e)}", exc_info=True)
        return render_template('error.html',
                               error_title='Trend Analysis Error',
                               error='Failed to load trend analysis'), 500

index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def process_data(csv_path):
    df = pd.read_csv(csv_path)
    # Ensure consistent datetime parsing
    df['exe_date'] = pd.to_datetime(df['exe_date'], format='%d-%m-%Y')
    df['max_batch_end_dt'] = pd.to_datetime(df['max_batch_end_dt'], format='%d-%m-%Y %H:%M')
    
    # Add normalized time columns for consistent comparison
    df['end_time'] = df['max_batch_end_dt'].dt.time
    df['end_hour_float'] = df['max_batch_end_dt'].dt.hour + df['max_batch_end_dt'].dt.minute/60
    
    return df

# Read the CSV file
df = process_data('dag_data.csv')

# Get unique dates for x-axis
unique_dates = sorted(df['exe_date'].unique())
date_strings = [d.strftime('%d-%m-%y') for d in unique_dates]

# Define time intervals for y-axis
time_intervals = [
    time(0, 0), time(3, 0), time(6, 0), time(9, 0),
    time(12, 0), time(15, 0), time(18, 0), time(21, 0), time(23, 59)
]
time_labels = [t.strftime('%H:%M') for t in time_intervals[:-1]] + ['24:00']

# Define thresholds for each application
thresholds = {
    'east': 7 + 0/60,  # 7:00 AM
    'north': 22 + 10/60,  # 22:10
    'south': 14 + 0/60,  # 14:00
    'west': 21 + 0/60  # 21:00
}

# App layout remains the same
layout = html.Div(className='main-container', children=[
    html.Div(className='header', children=[
        html.H1('DAG Execution Timeline', style={'color': '#ffffff'})  # White text
    ]),
    html.Div(className='dropdown-container', children=[
        html.Div([
            html.Label('Select Application:', 
                      style={'fontSize': '14px', 'fontWeight': 'bold', 
                            'color': '#51504f', 'marginRight': '10px'}),  # Dark Gray text
            dcc.Dropdown(
                id='app-dropdown',
                options=[{'label': 'All Applications', 'value': 'all'}] +
                        [{'label': app, 'value': app} 
                         for app in df['application_name'].unique()],
                value='all',
                style={'width': '300px'}
            )
        ]),
        html.Div([
            html.Label('Select DAG:', 
                      style={'fontSize': '14px', 'fontWeight': 'bold', 
                            'color': '#51504f', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='dag-dropdown',
                options=[],
                value=None,
                style={'width': '300px'},
                placeholder='Select a DAG'
            )
        ], style={'display': 'none'}, id='dag-dropdown-container')
    ]),
    html.Div(className='content-container', children=[
        dcc.Graph(id='time-series-graph', 
                style={'height': '700px'},
                config={
                    'displayModeBar': False,
                    'displaylogo': False})
    ])
])

def register_callbacks(app):
    @app.callback(
        Output('dag-dropdown-container', 'style'),
        Output('dag-dropdown', 'options'),
        Input('app-dropdown', 'value')
    )
    def update_dag_dropdown(selected_app):
        if selected_app == 'all':
            return {'display': 'none'}, []
        else:
            filtered_df = df[df['application_name'] == selected_app]
            dag_options = [{'label': dag, 'value': dag} for dag in filtered_df['dag_name'].unique()]
            return {'display': 'block'}, dag_options

    @app.callback(
        Output('time-series-graph', 'figure'),
        Input('app-dropdown', 'value'),
        Input('dag-dropdown', 'value')
    )
    def update_graph(selected_app, selected_dag):
        if selected_app == 'all':
            filtered_df = df
        else:
            filtered_df = df[df['application_name'] == selected_app]
            if selected_dag:
                filtered_df = filtered_df[filtered_df['dag_name'] == selected_dag]
        
        # Get the maximum end time for each date using the normalized time
        daily_max_indices = filtered_df.groupby('exe_date')['end_hour_float'].idxmax()
        daily_max = filtered_df.loc[daily_max_indices].reset_index(drop=True)
        
        # Create the figure
        fig = go.Figure()
        
        # Add the main scatter trace
        fig.add_trace(go.Scatter(
            x=[d.strftime('%d-%m-%y') for d in daily_max['exe_date']],
            y=daily_max['end_hour_float'],
            mode='lines+markers',
            name='Max Batch End Time',
            line=dict(color='#017cee', width=2),
            marker=dict(
                size=10,
                symbol='circle',
                line=dict(color='#fff', width=2)
            ),
            hovertemplate=(
                'Date: %{x}<br>'
                'Time: %{text}<br>'
                'DAG: %{customdata[0]}<br>'
                'Batch: %{customdata[1]}<br>'
                '<extra></extra>'
            ),
            text=[t.strftime('%H:%M') for t in daily_max['max_batch_end_dt']],
            customdata=list(zip(daily_max['dag_name'], daily_max['batch_name']))
        ))
        
        # Update layout
        fig.update_layout(
            title=None,
            xaxis=dict(
                title='Execution Date',
                gridcolor='#e0e0e0',
                showgrid=True,
                ticktext=date_strings,
                tickvals=date_strings,
                tickangle=90,
                tickmode='array',
                type='category',
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title='Time of Day',
                ticktext=time_labels,
                tickvals=[0, 3, 6, 9, 12, 15, 18, 21, 24],
                gridcolor='#e0e0e0',
                showgrid=True,
                range=[-0.5, 24.5],
                tickfont=dict(size=12)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            showlegend=False,
            margin=dict(b=100, l=60, r=20, t=40),
            height=650,
            width=1600
        )
        
        # Add reference lines
        for hour in [0, 3, 6, 9, 12, 15, 18, 21, 24]:
            fig.add_hline(
                y=hour,
                line=dict(color='#e0e0e0', width=1, dash='dash'),
                opacity=0.7
            )
        
        # Add threshold line if an application is selected
        if selected_app != 'all' and selected_app in thresholds:
            fig.add_hline(
                y=thresholds[selected_app],
                line=dict(color='red', width=2, dash='dash'),
                annotation_text=f'Threshold: {time(int(thresholds[selected_app]), int((thresholds[selected_app] % 1) * 60)).strftime("%H:%M")}',
                annotation_position='top left'
            )
        
        return fig