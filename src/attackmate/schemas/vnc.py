from typing import Optional, Literal
from .base import BaseCommand, StringNumber
from pydantic import model_validator, field_validator, ValidationInfo




class VncCommand(BaseCommand):

    type: Literal['vnc']
    cmd: Literal['key', 'type', 'move', 'capture', 'click', 'expectscreen', "close"]
    hostname: Optional[str] = None
    port: Optional[StringNumber] = None
    display: Optional[StringNumber] = None
    password: Optional[str] = None
    key: Optional[str] = None
    input: Optional[str] = None
    filename: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    creates_session: Optional[str] = None
    session: Optional[str] = None
    maxrms: Optional[float] = 0

    @model_validator(mode='after')
    def check_cmd_requirements(cls, values):
        cmd = values.cmd

        if values.background:
            raise ValueError('background mode is unsupported for VNC')
        if values.creates_session is not None and values.session is not None:
            raise ValueError('Cannot specify both "creates_session" and "session" at the same time.')
        
        required_fields = {
        "type": ["input"],
        "key": ["key"],
        "capture": ["filename"],
        "expectscreen": ["filename"],
        "move": ["x", "y"],
        }   

        if cmd in required_fields:
            missing_fields = [field for field in required_fields[cmd] if getattr(values, field, None) is None]
            if missing_fields:
                raise ValueError(f'Command "{cmd}" requires {", ".join(missing_fields)} field(s).')

        return values
