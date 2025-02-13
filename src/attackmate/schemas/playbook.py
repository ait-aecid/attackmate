from typing import List, Optional, Dict, Union
from .base import StrInt
from pydantic import BaseModel
from .sleep import SleepCommand
from .shell import ShellCommand
from .setvar import SetVarCommand
from .include import IncludeCommand
from .loop import LoopCommand
from .metasploit import MsfModuleCommand, MsfSessionCommand, MsfPayloadCommand

from .sliver import (
    SliverSessionCDCommand,
    SliverSessionLSCommand,
    SliverSessionNETSTATCommand,
    SliverSessionEXECCommand,
    SliverSessionMKDIRCommand,
    SliverSessionSimpleCommand,
    SliverSessionDOWNLOADCommand,
    SliverSessionUPLOADCommand,
    SliverSessionPROCDUMPCommand,
    SliverSessionRMCommand,
    SliverSessionTERMINATECommand,
    SliverHttpsListenerCommand,
    SliverGenerateCommand,
)
from .ssh import SSHCommand, SFTPCommand
from .http import WebServCommand, HttpClientCommand
from .father import FatherCommand
from .tempfile import TempfileCommand
from .debug import DebugCommand
from .regex import RegExCommand
from .vnc import VncCommand
from .json import JsonCommand

Command = Union[
    ShellCommand,
    MsfModuleCommand,
    MsfSessionCommand,
    MsfPayloadCommand,
    SleepCommand,
    SSHCommand,
    FatherCommand,
    SFTPCommand,
    DebugCommand,
    SetVarCommand,
    RegExCommand,
    TempfileCommand,
    IncludeCommand,
    LoopCommand,
    WebServCommand,
    HttpClientCommand,
    JsonCommand,
    SliverSessionCDCommand,
    SliverSessionLSCommand,
    SliverSessionNETSTATCommand,
    SliverSessionEXECCommand,
    SliverSessionMKDIRCommand,
    SliverSessionSimpleCommand,
    SliverSessionDOWNLOADCommand,
    SliverSessionUPLOADCommand,
    SliverSessionPROCDUMPCommand,
    SliverSessionRMCommand,
    SliverSessionTERMINATECommand,
    SliverHttpsListenerCommand,
    SliverGenerateCommand,
    VncCommand,
]


Commands = List[Command]


class Playbook(BaseModel):
    vars: Optional[Dict[str, List[StrInt] | StrInt]] = None
    commands: Commands
