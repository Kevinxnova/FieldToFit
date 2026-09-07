"""MCP stdio-to-HTTP bridge. No database access; stdout contains only JSON-RPC."""
import json
import os
import sys
import urllib.error
import urllib.request


def main():
    endpoint = os.getenv('METIS_MCP_URL', 'http://127.0.0.1:8000/api/mcp')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-11-25'}
    if os.getenv('METIS_READ_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['METIS_READ_TOKEN']
    for line in sys.stdin:
        message = None
        try:
            message = json.loads(line)
            req = urllib.request.Request(endpoint, data=json.dumps(message).encode(), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read()
                if raw:
                    result = json.loads(raw)
                    print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(f'Metis connection failed: {type(exc).__name__}', file=sys.stderr, flush=True)
            if isinstance(message, dict) and 'id' in message:
                print(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': -32603, 'message': 'Metis connection failed; check endpoint and read token'}}), flush=True)


if __name__ == '__main__':
    main()
