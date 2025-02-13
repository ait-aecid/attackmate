import pytest
from unittest.mock import MagicMock, patch
from attackmate.executors.vnc.vncexecutor import VncExecutor
from attackmate.schemas.vnc import VncCommand
from attackmate.variablestore import VariableStore
from attackmate.processmanager import ProcessManager
from attackmate.execexception import ExecException
from vncdotool.client import AuthenticationError


@pytest.fixture
def mock_process_manager():
    return MagicMock(spec=ProcessManager)


@pytest.fixture
def mock_variable_store():
    return MagicMock(spec=VariableStore)


@pytest.fixture
def vnc_executor(mock_process_manager, mock_variable_store):
    return VncExecutor(mock_process_manager, varstore=mock_variable_store)


@pytest.fixture
def mock_vnc_client():
    return MagicMock()


def test_vnc_connect_success(vnc_executor, mock_vnc_client, mocker):
    command = VncCommand(
        type='vnc',
        cmd='key',
        hostname='192.168.10.134',
        password='password',
        key='a'
    )

    mocker.patch('vncdotool.api.connect', return_value=mock_vnc_client)
    mock_vnc_client.protocol.connected = True  # Mock successful connection

    result = vnc_executor._exec_cmd(command)
    
    assert result.stdout == 'vnc_connected'
    mock_vnc_client.keyPress.assert_called_once_with('a')


def test_vnc_create_and_use_session(vnc_executor, mock_vnc_client, mocker):
    command_create = VncCommand(
        type='vnc',
        cmd='key',
        hostname='192.168.10.134',
        password='password',
        key='a',
        creates_session='session1'
    )

    command_use = VncCommand(
        type='vnc',
        cmd='key',
        session='session1',
        key='b'
    )

    mocker.patch('vncdotool.api.connect', return_value=mock_vnc_client)
    mock_vnc_client.protocol.connected = True  # Mock successful connection

    # Create session
    vnc_executor._exec_cmd(command_create)

    # Use session
    result = vnc_executor._exec_cmd(command_use)

    assert result.stdout == 'vnc_connected'
    mock_vnc_client.keyPress.assert_any_call('a')
    mock_vnc_client.keyPress.assert_any_call('b')


