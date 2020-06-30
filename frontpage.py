from app import app
import dash_html_components as html


def generate_frontpage(title):
    return(
            html.Div([
                html.Div(id='las-header', children=[
                    html.Div(
                        id='logo',
                        children=[
                            
                            html.A(
                                html.Img(
                                    id='logo-image',
                                    src=app.get_asset_url('logo.PNG'),
                                ), href='https://www.lenenergo.ru/'
                            )
                        ]
                    ),
                    html.P(
                        "Расчет технических потерь в системе УПЭ",
                        id='system-name'
                    )
                ]),
                html.Div(
                    id='las-header-text',
                    children=[
                        html.H2(title)]
                )
            ])
        )