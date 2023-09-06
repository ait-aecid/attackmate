import re
import time
import logging
from .schemas import BaseCommand
from .variablestore import VariableStore
from typing import Any
import copy


class ExecException(Exception):
    """ Exception for all Executors

    This exception is raised by Executors if anything
    goes wrong. The BaseExecutor will catch the
    Exception, writes it to the console and exits
    gracefully.

    """
    pass


class Result:
    """

    Instances of this Result-class will be returned
    by the Executors. It stores the standard-output
    and the returncode.
    """
    stdout: str
    returncode: int

    def __init__(self, stdout, returncode):
        """ Constructor of the Result

        Instances of this Result-class will be returned
        by the Executors. It stores the standard-output
        and the returncode.

        Parameters
        ----------
        stdout : str
            The standard-output of a command.
        returncode : int
            The returncode of a previous executed command
        """
        self.stdout = stdout
        self.returncode = returncode


class BaseExecutor:
    """

    The BaseExecutor is the base class of all Executors.
    It enables base functionality for all Executors and
    provides a structure for all Executors.

    In order to create a custom Executor, one must simply
    derive from the BaseExecutor and implement the method
    _exec_cmd()

    """
    def __init__(self, variablestore: VariableStore, cmdconfig=None):
        """ Constructor for BaseExecutor

        Parameters
        ----------
        cmdconfig : str, default `None`
            cmd_config settings.

        """
        self.logger = logging.getLogger('playbook')
        self.cmdconfig = cmdconfig
        self.output = logging.getLogger("output")
        self.varstore = variablestore

    def replace_variables(self, command: BaseCommand) -> BaseCommand:
        """ Replace variables using the VariableStore

        Replace all template-variables of the BaseCommand and return
        a new BaseCommand with all variables replaced with their values.

        Parameters
        ----------
        command : BaseCommand
            BaseCommand where all variables should be replaced

        Returns
        -------
        BaseCommand
            BaseCommand with replaced variables
        """
        template_cmd = copy.deepcopy(command)
        for member in command.list_template_vars():
            cmd_member = getattr(command, member)
            if isinstance(cmd_member, str):
                replaced_str = self.varstore.substitute(cmd_member)
                setattr(template_cmd, member, replaced_str)
            if isinstance(cmd_member, dict):
                # copy the dict to avoid referencing the original dict
                new_cmd_member = copy.deepcopy(cmd_member)
                for k, v in new_cmd_member.items():
                    if isinstance(v, str):
                        new_cmd_member[k] = self.varstore.substitute(v)
                setattr(template_cmd, member, new_cmd_member)
        return template_cmd

    def run(self, command: BaseCommand):
        """ Execute the command

        This method is executed by AttackMate and
        executes the given command. This method sets the
        run_count to 1 and runs the method exec(). Please note
        that this function will exchange all variables of the BaseCommand
        with the values of the VariableStore!

        Parameters
        ----------
        command : BaseCommand
            The settings for the command to execute

        """
        self.run_count = 1
        self.logger.debug(f"Template-Command: '{command.cmd}'")
        self.exec(self.replace_variables(command))

    def log_command(self, command):
        """ Log starting-status of the command

        """
        self.logger.info(f"Executing '{command}'")

    def save_output(self, command: BaseCommand, result: Result):
        """ Save output of command to a file. This method will
            ignore all exceptions and won't stop the programm
            on error.
        """
        if command.save:
            try:
                with open(command.save, "w") as outfile:
                    outfile.write(result.stdout)
            except Exception as e:
                self.logger.warn(f"Unable to write output to file {command.save}: {e}")

    def exec(self, command: BaseCommand):
        try:
            self.log_command(command)
            result = self._exec_cmd(command)
        except ExecException as error:
            result = Result(error, 1)
        if result.returncode != 0 and command.exit_on_error:
            self.logger.error(result.stdout)
            self.logger.debug("Exiting because return-code is not 0")
            exit(1)
        self.varstore.set_variable("RESULT_STDOUT", result.stdout)
        self.varstore.set_variable("RESULT_RETURNCODE", str(result.returncode))
        self.output.info(f"Command: {command.cmd}\n{result.stdout}")
        self.save_output(command, result)
        self.error_if(command, result)
        self.error_if_not(command, result)
        self.loop_if(command, result)
        self.loop_if_not(command, result)

    def error_if(self, command: BaseCommand, result: Result):
        if command.error_if is not None:
            m = re.search(command.error_if, result.stdout, re.MULTILINE)
            if m is not None:
                self.logger.error(
                        f"Exitting because error_if matches: {m.group(0)}"
                        )
                exit(1)

    def error_if_not(self, command: BaseCommand, result: Result):
        if command.error_if_not is not None:
            m = re.search(command.error_if_not, result.stdout, re.MULTILINE)
            if m is None:
                self.logger.error(
                        "Exitting because error_if_not does not match"
                        )
                exit(1)

    def loop_if(self, command: BaseCommand, result: Result):
        if command.loop_if is not None:
            m = re.search(command.loop_if, result.stdout, re.MULTILINE)
            if m is not None:
                self.logger.warn(
                        f"Re-run command because loop_if matches: {m.group(0)}"
                        )
                if self.run_count < self.variable_to_int("loop_count", command.loop_count):
                    self.run_count = self.run_count + 1
                    time.sleep(self.cmdconfig.loop_sleep)
                    self.exec(command)
                else:
                    self.logger.error("Exitting because loop_count exceeded")
                    exit(1)
            else:
                self.logger.debug("loop_if does not match")

    def loop_if_not(self, command: BaseCommand, result: Result):
        if command.loop_if_not is not None:
            m = re.search(command.loop_if_not, result.stdout, re.MULTILINE)
            if m is None:
                self.logger.warn(
                        "Re-run command because loop_if_not does not match"
                        )
                if self.run_count < self.variable_to_int("loop_count", command.loop_count):
                    self.run_count = self.run_count + 1
                    time.sleep(self.cmdconfig.loop_sleep)
                    self.exec(command)
                else:
                    self.logger.error("Exitting because loop_count exceeded")
                    exit(1)
            else:
                self.logger.debug("loop_if_not does not match")

    def variable_to_int(self, variablename: str, value: str) -> int:
        if value.isnumeric():
            return int(value)
        else:
            raise ExecException(f"Variable {variablename} has not a numeric value: {value}")

    def _exec_cmd(self, command: Any) -> Result:
        return Result(None, None)
