"""MCP stdio-to-HTTP bridge. No database access; stdout contains only JSON-RPC."""
import json
import os
import socket
import ssl
import sys
import urllib.error
import urllib.request


def tls_context():
    """Honor explicit trust configuration; supplement only an empty default store."""
    context = ssl.create_default_context()
    if not (os.getenv('SSL_CERT_FILE') or os.getenv('SSL_CERT_DIR')) and not context.get_ca_certs():
        try:
            import certifi
        except ImportError:
            pass
        else:
            context.load_verify_locations(cafile=certifi.where())
    return context


def diagnostic(exc):
    """Never expose exception text: it may contain a URL, token or response body."""
    if isinstance(exc, urllib.error.HTTPError):
        status = exc.code
        advice = {
            401: 'Configure FIELDTOFIT_READ_TOKEN with a read token, not an administrator password.',
            403: 'Check read permissions and allowed origins.',
            404: 'Check FIELDTOFIT_MCP_URL; the public endpoint is /api/mcp/curated.',
            405: 'Use a Streamable HTTP MCP endpoint, not a legacy SSE address.',
            406: 'The server requires both application/json and text/event-stream in Accept.',
            429: 'The service is rate limited; retry later.',
        }.get(status, 'The service failed; retry later.' if status >= 500 else 'Check the MCP endpoint and protocol settings.')
        return 'http_error', f'FieldToFit HTTP {status}. {advice}'
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, ssl.SSLCertVerificationError):
        return 'tls_certificate_error', 'TLS certificate verification failed. Install Python trusted certificates or set SSL_CERT_FILE to a trusted CA bundle. Do not disable TLS verification.'
    if isinstance(reason, ssl.SSLError):
        return 'tls_error', 'TLS connection failed. Check the server certificate and trusted CA configuration.'
    if isinstance(reason, socket.gaierror):
        return 'dns_error', 'Cannot resolve the MCP hostname. Check the address and DNS/network connection.'
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return 'timeout', 'The MCP request timed out. Check the network, retry, and use summary/chunk reading for large collections.'
    if isinstance(reason, (json.JSONDecodeError, UnicodeError, ValueError)):
        return 'invalid_response', 'The endpoint returned an invalid MCP response. Check the URL and any proxy or sign-in page.'
    if isinstance(reason, (FileNotFoundError, PermissionError)):
        return 'ca_configuration_error', 'Cannot load the configured TLS certificates. Check SSL_CERT_FILE and SSL_CERT_DIR.'
    return 'connection_error', 'Cannot connect to FieldToFit. Check the endpoint and network; no credentials or server response have been logged.'


def main():
    endpoint = os.getenv('FIELDTOFIT_MCP_URL', 'http://127.0.0.1:8000/api/mcp')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if os.getenv('FIELDTOFIT_READ_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['FIELDTOFIT_READ_TOKEN']
    for line in sys.stdin:
        message = None
        try:
            message = json.loads(line)
            if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or not isinstance(message.get('method'), str):
                raise ValueError('Invalid local JSON-RPC request')
            req = urllib.request.Request(endpoint, data=json.dumps(message).encode(), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=60, context=tls_context()) as response:
                raw = response.read()
                if 'id' in message:
                    result = json.loads(raw)
                    if (not isinstance(result, dict) or result.get('jsonrpc') != '2.0' or result.get('id') != message['id']
                            or ('result' in result) == ('error' in result)):
                        raise ValueError('Invalid remote JSON-RPC response')
                    if message['method'] == 'initialize' and isinstance(result.get('result'), dict):
                        protocol = result['result'].get('protocolVersion')
                        if isinstance(protocol, str):
                            headers['MCP-Protocol-Version'] = protocol
                    print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            category, advice = diagnostic(exc)
            print(f'FieldToFit [{category}]: {advice}', file=sys.stderr, flush=True)
            if isinstance(message, dict) and 'id' in message:
                print(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': -32603, 'message': advice, 'data': {'code': category}}}), flush=True)


if __name__ == '__main__':
    main()
