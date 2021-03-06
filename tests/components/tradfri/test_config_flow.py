"""Test the Tradfri config flow."""
from unittest.mock import patch

import pytest

from homeassistant import data_entry_flow
from homeassistant.components.tradfri import config_flow

from tests.common import mock_coro


@pytest.fixture
def mock_auth():
    """Mock authenticate."""
    with patch('homeassistant.components.tradfri.config_flow.'
               'authenticate') as mock_auth:
        yield mock_auth


@pytest.fixture
def mock_gateway_info():
    """Mock get_gateway_info."""
    with patch('homeassistant.components.tradfri.config_flow.'
               'get_gateway_info') as mock_gateway:
        yield mock_gateway


@pytest.fixture
def mock_entry_setup():
    """Mock entry setup."""
    with patch('homeassistant.components.tradfri.'
               'async_setup_entry') as mock_setup:
        mock_setup.return_value = mock_coro(True)
        yield mock_setup


async def test_user_connection_successful(hass, mock_auth, mock_entry_setup):
    """Test a successful connection."""
    mock_auth.side_effect = lambda hass, host, code: mock_coro({
        'host': host,
        'gateway_id': 'bla'
    })

    flow = await hass.config_entries.flow.async_init(
        'tradfri', context={'source': 'user'})

    result = await hass.config_entries.flow.async_configure(flow['flow_id'], {
        'host': '123.123.123.123',
        'security_code': 'abcd',
    })

    assert len(mock_entry_setup.mock_calls) == 1

    assert result['type'] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result['result'].data == {
        'host': '123.123.123.123',
        'gateway_id': 'bla',
        'import_groups': False
    }


async def test_user_connection_timeout(hass, mock_auth, mock_entry_setup):
    """Test a connection timeout."""
    mock_auth.side_effect = config_flow.AuthError('timeout')

    flow = await hass.config_entries.flow.async_init(
        'tradfri', context={'source': 'user'})

    result = await hass.config_entries.flow.async_configure(flow['flow_id'], {
        'host': '127.0.0.1',
        'security_code': 'abcd',
    })

    assert len(mock_entry_setup.mock_calls) == 0

    assert result['type'] == data_entry_flow.RESULT_TYPE_FORM
    assert result['errors'] == {
        'base': 'timeout'
    }


async def test_user_connection_bad_key(hass, mock_auth, mock_entry_setup):
    """Test a connection with bad key."""
    mock_auth.side_effect = config_flow.AuthError('invalid_security_code')

    flow = await hass.config_entries.flow.async_init(
        'tradfri', context={'source': 'user'})

    result = await hass.config_entries.flow.async_configure(flow['flow_id'], {
        'host': '127.0.0.1',
        'security_code': 'abcd',
    })

    assert len(mock_entry_setup.mock_calls) == 0

    assert result['type'] == data_entry_flow.RESULT_TYPE_FORM
    assert result['errors'] == {
        'security_code': 'invalid_security_code'
    }


async def test_discovery_connection(hass, mock_auth, mock_entry_setup):
    """Test a connection via discovery."""
    mock_auth.side_effect = lambda hass, host, code: mock_coro({
        'host': host,
        'gateway_id': 'bla'
    })

    flow = await hass.config_entries.flow.async_init(
        'tradfri', context={'source': 'discovery'}, data={
            'host': '123.123.123.123'
        })

    result = await hass.config_entries.flow.async_configure(flow['flow_id'], {
        'security_code': 'abcd',
    })

    assert len(mock_entry_setup.mock_calls) == 1

    assert result['type'] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result['result'].data == {
        'host': '123.123.123.123',
        'gateway_id': 'bla',
        'import_groups': False
    }


async def test_import_connection(hass, mock_gateway_info, mock_entry_setup):
    """Test a connection via import."""
    mock_gateway_info.side_effect = \
        lambda hass, host, identity, key: mock_coro({
            'host': host,
            'identity': identity,
            'key': key,
            'gateway_id': 'mock-gateway'
        })

    result = await hass.config_entries.flow.async_init(
        'tradfri', context={'source': 'import'}, data={
            'host': '123.123.123.123',
            'identity': 'mock-iden',
            'key': 'mock-key',
            'import_groups': True
        })

    assert result['type'] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result['result'].data == {
        'host': '123.123.123.123',
        'gateway_id': 'mock-gateway',
        'identity': 'mock-iden',
        'key': 'mock-key',
        'import_groups': True
    }

    assert len(mock_gateway_info.mock_calls) == 1
    assert len(mock_entry_setup.mock_calls) == 1
