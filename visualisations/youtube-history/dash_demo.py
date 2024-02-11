import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd

import visual_plot

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1('YouTube History Visualisation'),
    html.H2('Instructions'),
    html.Ol([
        html.Li(['Go to ', html.A('Google Takout', href='https://takeout.google.com/')]),
        html.Li(['Deselect all']),
        html.Li(['Select YouTube']),
        html.Li(['Underneath YouTube, click on "All YouTube Data Included"']),
        html.Li(['Deselect All']),
        html.Li(['Select History']),
        html.Li(['Once downloaded, upload below']),
    ]),
    html.H2('Upload'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename:
            df = pd.read_json(io.StringIO(decoded.decode('utf-8')), orient='records')
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    model = visual_plot.HistoryVisualiser(df)
    model.preprocess_df()
    model.gen_ngrams()
    fig = model.get_fig()
    return html.Div([
        html.Div([
            html.H2('Summary'),
            html.Plaintext('Loaded file: {}'.format(filename)),
            html.Plaintext('Time of Load: {}'.format(datetime.datetime.fromtimestamp(date))),
            html.Plaintext('Found {} entries'.format(len(df))),
            html.H2('Visualisation'),
            html.Hr()  # horizontal line
        ]),
        dcc.Graph(
            id='test',
            figure=fig
        )
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children



if __name__ == '__main__':
    app.run_server(debug=True)