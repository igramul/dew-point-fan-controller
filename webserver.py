
HTML = """<!DOCTYPE html>
<html>
    <head> <title>Dew Point Fan Controller</title> </head>
    <body> <h1>Dew Point Fan Controller</h1>
        <p>%s</p>
    </body>
</html>
"""


async def serve_client(reader, writer):
    # Client connected
    request_line = await reader.readline()
    print('Request:', request_line)
    # not interested in HTTP request headers, skip them
    while await reader.readline() != b'\r\n':
        pass

    request = str(request_line)
    metrics = request.find('/metrics')

    if metrics == 6:
        response = dew_point_fan_controller.get_metrics()
    else:
        response = HTML % f'<pre>{dew_point_fan_controller.get_measure_html()}</pre>'

    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    # Client disconnected