from flask import Flask, request, Response, abort
import ipaddress
import requests


def get_ip_range(cidr):
    try:
        return [str(ip) for ip in ipaddress.IPv4Network(cidr)]
    except:
        print(cidr)
        return ''


def read_proxy_target():
    f = open("./proxy.txt", "rt")
    lines = f.readlines()
    res = ''
    for line in lines:
        line = line.replace('\n', '')
        line = line.rstrip()
        res = line

    f.close()
    return res


def read_api_tokens():
    f = open("./api_token.txt", "rt")
    res = []
    lines = f.readlines()

    for line in lines:
        line = line.replace('\n', '')
        line = line.rstrip()
        api_token_map[line] = '1'

    f.close()
    return res


def read_whitelist():
    f = open("./whitelist.txt", "rt")
    res = []
    lines = f.readlines()

    for line in lines:
        line = line.replace('\n', '')
        line = line.rstrip()
        for real in get_ip_range(line):
            ip_map[real] = 1

    f.close()
    return res


print('starting server ..')

ip_map = {}
api_token_map = {}
proxy_target = read_proxy_target()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

read_whitelist()
read_api_tokens()

print('server is started')


def _proxy(*args, **kwargs):
    url = request.url.replace(request.host_url, proxy_target)
    headers = {key: value for (key, value) in request.headers if key != 'Host'}

    print(headers)
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response


def limit_remote_addr(request):
    remote = request.remote_addr

    if remote in ip_map:
        return

    abort(403)  # Forbidden


@app.route('/ips', methods=['POST'])
def post_ip():
    if 'X-PROXY-TOKEN' not in request.headers:
        abort(403)

    token = request.headers['X-PROXY-TOKEN']
    if token not in api_token_map:
        abort(403)

    remote = request.remote_addr
    ip_map[remote] = 1
    print(ip_map)
    return 'ok'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def hello_world(path):
    limit_remote_addr(request)
    t = request.url.replace(request.host_url, proxy_target)
    print(request.url + " -> " + t)
    return _proxy(request)


if __name__ == '__main__':
    app.run(debug=False)
