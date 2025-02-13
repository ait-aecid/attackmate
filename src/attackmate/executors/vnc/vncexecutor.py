"""
vncexecutor.py
============================================
This class enables executing commands via vnc.
It utilizes the vncdotool. https://github.com/sibson/vncdotool (can be installed with pip)

the vnc client connection_string needs to be in the format address[:display|::port]

"""

from attackmate.executors.baseexecutor import BaseExecutor
from attackmate.execexception import ExecException
from attackmate.result import Result
from attackmate.variablestore import VariableStore
from attackmate.processmanager import ProcessManager
from attackmate.schemas.vnc import VncCommand
from vncdotool import api
from vncdotool.client import AuthenticationError
from attackmate.executors.vnc.sessionstore import SessionStore
from attackmate.executors.executor_factory import executor_factory
import time

@executor_factory.register_executor('vnc')
class VncExecutor(BaseExecutor):
    def __init__(self, pm: ProcessManager, cmdconfig=None, *, varstore: VariableStore):
        self.session_store = SessionStore()
        self.set_defaults()
        super().__init__(pm, varstore, cmdconfig)

    def set_defaults(self):
        self.hostname = None
        self.port = None
        self.display = None
        self.password = None


    def build_connection_string(self) -> str:
        if not self.hostname:
            raise ExecException("Hostname is required for VNC connection.")
        connection_str = self.hostname
        if self.display is not None:
            connection_str += f":{self.display}"
        elif self.port is not None:
            connection_str += f"::{self.port}"
        return connection_str

    def connect(self, command: VncCommand) -> api.ThreadedVNCClientProxy:
        

        client = api.connect(self.build_connection_string(), command.password)
        time.sleep(5)
        if not (client and client.protocol and client.protocol.connected):  
            self.logger.info(f"Could not connect to VNC server: {self.build_connection_string()}")
            client.disconnect()
            return None
        else:
            return client

    def connect_use_session(self, command):

        if command.creates_session is not None:
            # If 'creates_session' is specified, create a new session and save it
            client = self.connect(command)
            if not client:
                return None
            self.session_store.set_session(command.creates_session, client)
            return client

        if command.session is not None:
            # If 'session' is specified, check if it exists, else raise an error
            if not self.session_store.has_session(command.session):
                raise ExecException(f'VNC-Session not in Session-Store: {command.session}')
            else:
                return self.session_store.get_client_by_session(command.session)

        # If neither 'creates_session' nor 'session' is provided
        default_session = 'default'

        if not self.session_store.has_session(default_session):
            # Create default session if it doesn't exist
            client = self.connect(command)
            self.session_store.set_session(default_session, client)
        else:
            # Retrieve the default session if it already exists
            client = self.session_store.get_client_by_session(default_session)

        return client

    def cache_settings(self, command: VncCommand):
        if command.hostname:
            self.hostname = command.hostname
        if command.port:
            self.port = command.port
        if command.display:
            self.display = command.display
        if command.password:
            self.password = command.password

    def log_command(self, command: VncCommand):
        self.cache_settings(command)
        self.logger.info(f"Executing Vnc-Command: '{command.cmd}'. Host: {self.hostname}")

    def send_keys(self, client, keys):
        for k in keys:
            client.keyPress(k)

    def _exec_cmd(self, command: VncCommand) -> Result:
        self.cache_settings(command)
        output = ''
        
        try:
            client = self.connect_use_session(command)
            if not (client and client.protocol.connected):
                return Result(output, 0)

            actions = {
                "key": lambda: client.keyPress(command.key),
                "type": lambda: self.send_keys(client, command.input),
                "move": lambda: client.mouseMove(command.x, command.y),
                "capture": lambda: client.captureScreen(command.filename),
                "click": lambda: client.mousePress(1),
                "expectscreen": lambda: client.expectScreen(command.filename, command.maxrms),
                "close": lambda: self.close_connection(command.session),
            }
            action = actions.get(command.cmd)
            if action:
                action()
            else:
                raise ExecException(f"Unknown VNC command: {command.cmd}")
            
        except (ValueError, AttributeError, AuthenticationError, OSError) as e:
            raise ExecException(f"VNC Execution Error: {e}")

        output = "vnc_connected"
        return Result(output, 0)

    def close_connection(self, session_name: str = "default"):
        """Closes the VNC connection for a given session."""
        if self.session_store.has_session(session_name):
            client = self.session_store.get_client_by_session(session_name)
            if client:
                try:
                    self.logger.info(f"Closing VNC connection for session: {session_name}")
                    client.disconnect()
                    api.shutdown()
                    self.session_store.remove_session(session_name)
                    self.logger.info(f"VNC session '{session_name}' closed and removed.")
                except Exception as e:
                    self.logger.error(f"Error while closing VNC connection for session '{session_name}': {str(e)}")
                    raise ExecException(f"Error closing VNC connection: {e}")
        else:
            self.logger.warning(f"VNC session '{session_name}' not found in session store.")

                   