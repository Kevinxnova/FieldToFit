"""Bridge errors are actionable without printing secrets or weakening TLS."""
import io
import json
import socket
import ssl
import urllib.error
from unittest.mock import Mock

import pytest
from backend import mcp_stdio as bridge


@pytest.mark.parametrize('error,category',[
 (urllib.error.URLError(ssl.SSLCertVerificationError('secret-url')),'tls_certificate_error'),
 (urllib.error.URLError(socket.gaierror('secret-url')),'dns_error'),
 (urllib.error.URLError(TimeoutError('secret-url')),'timeout'),
 (ssl.SSLError('secret-url'),'tls_error'),
 (FileNotFoundError('secret-url'),'ca_configuration_error'),
 (ValueError('secret-url'),'invalid_response'),
 (OSError('secret-url'),'connection_error'),
 *[(urllib.error.HTTPError('https://secret-url',status,'secret-url',{},None),'http_error') for status in [401,403,404,405,406,429,500]],
])
def test_classified_errors_never_echo_private_details(error,category):
    code,advice=bridge.diagnostic(error)
    assert code==category and 'secret-url' not in advice


def test_empty_default_store_uses_installed_certifi(monkeypatch):
    monkeypatch.delenv('SSL_CERT_FILE',raising=False);monkeypatch.delenv('SSL_CERT_DIR',raising=False)
    context=Mock();context.get_ca_certs.return_value=[]
    monkeypatch.setattr(bridge.ssl,'create_default_context',lambda:context)
    assert bridge.tls_context() is context
    context.load_verify_locations.assert_called_once()


@pytest.mark.parametrize('explicit',['SSL_CERT_FILE','SSL_CERT_DIR'])
def test_explicit_ca_is_never_replaced(monkeypatch,explicit):
    monkeypatch.setenv(explicit,'/a/trusted/private/ca')
    context=Mock();context.get_ca_certs.return_value=[]
    monkeypatch.setattr(bridge.ssl,'create_default_context',lambda:context)
    bridge.tls_context();context.load_verify_locations.assert_not_called()


def test_system_trust_is_preserved(monkeypatch):
    context=Mock();context.get_ca_certs.return_value=[{'subject':'existing'}]
    monkeypatch.setattr(bridge.ssl,'create_default_context',lambda:context)
    bridge.tls_context();context.load_verify_locations.assert_not_called()


def test_stdout_protocol_notification_and_error_redaction(monkeypatch):
    lines=[{'jsonrpc':'2.0','id':1,'method':'initialize'}, {'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'}]
    monkeypatch.setattr(bridge.sys,'stdin',io.StringIO('\n'.join(json.dumps(x) for x in lines)))
    out=io.StringIO();err=io.StringIO();monkeypatch.setattr(bridge.sys,'stdout',out);monkeypatch.setattr(bridge.sys,'stderr',err)
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','private-test-token')
    context=Mock();monkeypatch.setattr(bridge,'tls_context',lambda:context)
    requests=[]
    def open_url(req,**kwargs):
        requests.append(req)
        assert kwargs['context'] is context and kwargs['timeout']==60
        if len(requests)==1:
            r=Mock();r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
            r.read.return_value=json.dumps({'jsonrpc':'2.0','id':1,'result':{'protocolVersion':'2025-06-18'}}).encode();return r
        assert req.get_header('Mcp-protocol-version')=='2025-06-18'
        raise urllib.error.HTTPError('https://host/private-test-token',401,'private-test-token',{},None)
    monkeypatch.setattr(bridge.urllib.request,'urlopen',open_url);bridge.main()
    data=[json.loads(x) for x in out.getvalue().splitlines()]
    assert len(data)==2 and [x['id'] for x in data]==[1,2]
    assert data[1]['error']['data']['code']=='http_error'
    assert 'private-test-token' not in out.getvalue()+err.getvalue()


def test_real_default_context_keeps_verification():
    context=bridge.tls_context()
    assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname
