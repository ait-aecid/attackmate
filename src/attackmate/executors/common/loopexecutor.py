"""
loopexecutor.py
============================================
Execute commands in a loop
"""

import copy
from typing import Callable
from string import Template
from attackmate.executors.baseexecutor import BaseExecutor
from attackmate.executors.features.conditional import Conditional
from attackmate.result import Result
from attackmate.schemas.loop import LoopCommand
from attackmate.schemas.playbook import Commands, Command
from attackmate.variablestore import VariableStore
from attackmate.execexception import ExecException
from attackmate.processmanager import ProcessManager
from attackmate.executors.executor_factory import executor_factory
import re


@executor_factory.register_executor('loop')
class LoopExecutor(BaseExecutor):
    def __init__(
        self,
        pm: ProcessManager,
        cmdconfig=None,
        *,
        varstore: VariableStore,
        runfunc: Callable[[Commands], None],
        substitute_cmd_vars=False,
    ):
        self.runfunc = runfunc
        super().__init__(pm, varstore, cmdconfig, substitute_cmd_vars)

    def log_command(self, command: LoopCommand):
        self.logger.info('Looping commands')

    def break_condition_met(self, command: LoopCommand, placeholders) -> bool:
        if not command.break_if:
            return False
        condition = Template(command.break_if).safe_substitute(placeholders)

        if Conditional.test(condition):
            self.logger.warning('Breaking out of loop due to condition: %s', command.break_if)
            return True
        return False

    def substitute_variables_in_command(self, command_obj, placeholders: dict):
        """
        Replaces all occurrences of placeholders in *any* string attribute
        of the command_obj with the values from placeholders.
        E.g. if placeholders = {'LOOP_ITEM': 'https://example.com'},
             and command_obj.url = '$LOOP_ITEM', then it becomes 'https://example.com'.
        """
        for attr_name, attr_val in vars(command_obj).items():
            if isinstance(attr_val, str) and "$" in attr_val:
                new_val = Template(attr_val).safe_substitute(placeholders)
                setattr(command_obj, attr_name, new_val)

    def loop_range(self, command: LoopCommand, start: int, end: int) -> None:
        for x in range(start, end):
            for cmd in command.commands:
                template_cmd: Command = copy.deepcopy(cmd)
                placeholders = {
                    'LOOP_INDEX': x,
                    **self.varstore.variables,
                }

                if self.break_condition_met(command, placeholders):
                    return
                self.substitute_variables_in_command(template_cmd, placeholders)
                self.runfunc([template_cmd])

    def loop_items(self, command: LoopCommand, varname: str, iterable: list[str]) -> None:
        for x in iterable:
            for cmd in command.commands:
                template_cmd: Command = copy.deepcopy(cmd)
                placeholders = {
                    'LOOP_ITEM': x,
                    **self.varstore.variables,
                }
                
                if self.break_condition_met(command, placeholders):
                    return
                self.substitute_variables_in_command(template_cmd, placeholders)
                self.runfunc([template_cmd])

    def loop_until(self, command: LoopCommand, condition: str) -> None:
        x = 0
        tpl = Template(condition)

        condition = tpl.safe_substitute(LOOP_INDEX=x, **self.varstore.variables)
        while not Conditional.test(condition):
            for cmd in command.commands:
                if not Conditional.test(tpl.safe_substitute(LOOP_INDEX=x, **self.varstore.variables)):
                    template_cmd: Command = copy.deepcopy(cmd)
                    temp = Template(template_cmd.cmd)
                    template_cmd.cmd = temp.safe_substitute(LOOP_INDEX=x, **self.varstore.variables)

                    self.runfunc([template_cmd])
                else:
                    return
            x += 1

    def execute_loop(self, command: LoopCommand) -> None:
        range_match = re.search(r'range\(\s*(\d+)\s*,\s*(\d+)\s*\)', command.cmd)
        if range_match:
            range_start, range_end = map(int, range_match.groups())
            if range_start > range_end:
                raise ExecException('range_start is bigger than range_end')
            self.loop_range(command, range_start, range_end)
            return

        items_match = re.search(r'items\(\s*([^\)]+)\s*\)', command.cmd)
        if items_match:
            var_name = items_match.group(1)
            listvar = self.varstore.get_list(var_name)
            if listvar is None:
                raise ExecException(f"List variable '{var_name}' does not exist")
            self.loop_items(command, var_name, listvar)
            return

        until_match = re.search(r'until\((.*)\)', command.cmd)
        if until_match:
            condition = until_match.group(1)
            self.logger.info('Loop until ' + condition)
            self.loop_until(command, condition)
            return

        self.logger.warning('No valid loop condition found in command: %s', command.cmd)

    def _exec_cmd(self, command: LoopCommand) -> Result:
        # idea: use runfunc with one command only
        # in that way it is possible to replace context-variables first
        # runfunc will replace global variables then
        self.execute_loop(command)
        self.logger.info('Loop execution complete')
        return Result('', 0)