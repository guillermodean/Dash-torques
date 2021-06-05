import pandas as pd
import numpy as np
import matplotlib as plt
import plotly.express as px
import plotly.graph_objs as go
from Classes.Filterdata import Filtrar
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_scripts = [
    'https://www.google-analytics.com/analytics.js',
    {'src': 'https://cdn.polyfill.io/v2/polyfill.min.js'},
    {
        'src': 'https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.10/lodash.core.js',
        'integrity': 'sha256-Qqd/EfdABZUcAxjOkMi8eGEivtdTkh3b65xCZL4qAQA=',
        'crossorigin': 'anonymous'
    }
]
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    {
        'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
        'crossorigin': 'anonymous'
    }
]
# ----------------------------------------------------------------------------
# importar data y tratar

df = pd.read_csv('Results_TTM.csv', sep=";", header=0)
df = df.drop(
    columns=["Controlling transducer", "Current min (A)", "Current max (A)", "Current min (%)", "Current max (%)",
             "Current (%)", "Torque rate", "Current (A)"])
# df = Filterdata.Filtrar(df)
df = df.drop(
    columns=["Step status", "Current trend", "Torque rate min", "Torque rate max", "Torque rate trend", "CVILOGIX",
             "Identifier6", "Identifier7", "Identifier8", "Identifier9", "Identifier10",
             "Second transducer torque deviation", "Second transducer angle deviation", "Result type", "Pulse counter",
             "Angle offset", "AO torque rate"])
df = df.rename(
    columns={"Result number": "Result_number", "Pset ID": "Pset_ID", "Step ID": "Step_ID", "Torque min": "Torque_min",
             "Torque max": "Torque_max", "Angle min": "Angle_min", "Angle max": "Angle_max",
             "Controller serial no.": "Controller_serial_no.", "Pset name": "Pset_name",
             'Controller name': 'Controller_name', 'Error code': 'Error_code', 'Result status': 'Result_status'})
df = df[~df["Pset_name"].str.contains("Poka", na=False)]
df.astype({'Time result': 'datetime64[ns, US/Eastern]'}).dtypes
df.reset_index(inplace=True)


# ----------------------------------------------------------------------------


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def generate_nok(dataframe):
    dataframe = dataframe[['Result_status', 'Result_number']].groupby(by='Result_status').count()
    print(dataframe)
    fig = px.pie(dataframe, names='Result_number', values='', title='% of torques not ok filtered by pset')
    return fig


app = dash.Dash(__name__, external_scripts=external_scripts,
                external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H4(children='ISRI TTM', style={'text-align': 'center'}),
    dcc.Dropdown(id='dropdown', options=[
        {'label': str(i), 'value': str(i)} for i in df['Pset_name'].unique()
    ], multi=True, placeholder='Filter by Pset...'),
    dcc.Graph(id='general_nok'),
    html.Br(),
    html.Div(id='table-container')
])


@app.callback(
    Output(component_id='table-container', component_property='children'),
    Input(component_id='dropdown', component_property='value'))
def display_table(dropdown_value):
    if dropdown_value is None:
        return generate_table(df)
    else:
        dff = df[df['Pset_name'].str.contains('|'.join(dropdown_value), na=False)]
        return generate_table(dff)


@app.callback(
    Output(component_id='general_nok', component_property='figure'),
    Input(component_id='dropdown', component_property='value'))
def display_nok_graph(dropdown_value):
    if dropdown_value is None:
        return generate_nok(df)
    else:
        dff = df[df['Pset_name'].str.contains('|'.join(dropdown_value), na=False)]
        return generate_table(dff)
    return generate_nok(dff)


if __name__ == '__main__':
    app.run_server(debug=True)
