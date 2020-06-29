#!/usr/bin/env python
# coding: utf-8

"""
Таблица:
сравнение расчета тех потерь в РТП-3 и алгоритм УПЭ
"""

import dash_table
import frontpage
import pandas as pd
import navigation_table
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app

df = pd.read_csv('data//flood.csv',
    usecols=['date', 'time_start', 'time_end', 'number_of_samples', 'val', 'standard', 'sampling_site'])
df = df.replace(',', '.', regex = True)
df['val'] = df['val'].astype('float64')
df['standard'] = df['standard'].astype('float64')
df['excess'] = round(df['val'] / df['standard'], 2)

column_names = [{"name": "Дата", "id": "date"},
                {"name": "Время начала отбора", "id": "time_start"},
                {"name": "Время окончания отбора", "id": "time_end"},
                {"name": "Номер пробы", "id": "number_of_samples"},
                {"name": "Кратность превышения", "id": "excess"},
                {"name": "Место отбора проб", "id": "sampling_site"}
                ]

PAGE_SIZE = 8

operators = [['ge ', '>='],
            ['le ', '<='],
            ['lt ', '<'],
            ['gt ', '>'],
            ['ne ', '!='],
            ['eq ', '='],
            ['contains '],
            ['datestartswith ']]

def generate_table():
    measure_table = dash_table.DataTable(
        id='datatable-paging',
        columns=column_names,

        page_current=0,
        page_size=PAGE_SIZE,
        page_action='custom',

        filter_action='custom',
        filter_query='',

        style_data={
            'textAlign': 'central',
            'whiteSpace': 'normal',
	        'height': 'auto',
        },
        css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 14px;
                max-height: 56px; min-height: 56px; height: 56px;
                display: block;
                overflow-y: hidden;
            '''
        }],
        style_cell={
            'textAlign': 'center',
	    'fontsize': '14px',
        },
        style_cell_conditional=[
            {
                'if': {
                    'filter_query': '{excess} > 100',
                },
                'backgroundColor': 'rgb(237, 151, 183)'
            },
            {
                'if': {'column_id': 'date'},
                'width': '100px'
            },
            {
                'if': {'column_id': 'time_start'},
                'width': '100px'
            },
            {
                'if': {'column_id': 'number_of_samples'},
                'width': '100px'
            },
            {
                'if': {'column_id': 'excess'},
                'width': '100px'
            }
        ]
    )

    return measure_table


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


layout = html.Div([
    frontpage.generate_frontpage("Данные по отбору проб"),
    generate_table(),
    navigation_table.table_link('/norilsk2', '/')
])


@app.callback(
    Output('datatable-paging', 'data'),
    [
        Input('datatable-paging', "page_current"),
        Input('datatable-paging', "page_size"),
        Input('datatable-paging', "filter_query")
    ]
)
def update_table(page_current,page_size, filter):
    print(filter)
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    return dff.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('records')
