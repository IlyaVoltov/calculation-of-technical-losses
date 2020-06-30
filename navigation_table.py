import dash_html_components as html
import base64


def table_link(backward_link, forward_link):
    table = html.Div(
       children=[
                html.A(
                    html.Img(
                        id='back',
                        src='data:image/JPG;base64,{}'.format(
                            base64.b64encode(open('assets/back.JPG', 'rb').read()).decode())
                    ), href=backward_link),
                html.A(
                    html.Img(
                        id='forward',
                        src='data:image/jpg;base64,{}'.format(
                            base64.b64encode(open('assets/forward.jpg', 'rb').read()).decode())
                    ), href=forward_link)]
        )

    return table