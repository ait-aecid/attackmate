import copy

from attackmate.result import Result
from attackmate.schemas.base import BaseCommand, StringNumber
from attackmate.variablestore import VariableStore
from attackmate.execexception import ExecException


class CmdVars:
    def __init__(self, variablestore: VariableStore):
        self.varstore = variablestore
        self.setoutputvars = True

    def set_result_vars(self, result: Result):
        if self.setoutputvars:
            self.varstore.set_variable('RESULT_STDOUT', result.stdout)
            self.varstore.set_variable('RESULT_RETURNCODE', str(result.returncode))

    def substitute_template_vars(self, command: BaseCommand, substitute_cmd_vars: bool = True) -> BaseCommand:
        """Replace variables using the VariableStore

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
        substituted_command = copy.deepcopy(command)
        for attr_name in command.list_template_vars():

            # Skip variable substitution for "cmd"
            if attr_name == 'cmd'  and not substitute_cmd_vars:
                continue 

            if attr_name == "break_if":
                continue 

            attr_value = getattr(command, attr_name)

            if isinstance(attr_value, str):
                substituted_value = self.varstore.substitute(attr_value)
                setattr(substituted_command, attr_name, substituted_value)

            elif isinstance(attr_value, dict):
                # copy the dict to avoid referencing the original dict
                substituted_dict = copy.deepcopy(attr_value)
                for k, v in substituted_dict.items():
                    if isinstance(v, str):
                        substituted_dict[k] = self.varstore.substitute(v)
                setattr(substituted_command, attr_name, substituted_dict)

            elif isinstance(attr_value, list):
                # copy the list to avoid referencing the original list
                substituted_list = [i for i in attr_value]
                for v in substituted_list:
                    if isinstance(v, str):
                        index = substituted_list.index(v)
                        substituted_list[index] = self.varstore.substitute(v)
                setattr(substituted_command, attr_name, substituted_list)
        return substituted_command

    @staticmethod
    def variable_to_int(variablename: str, value: StringNumber) -> int:
        if not value:
            raise ExecException(f'Variable {variablename} has not a numeric value: {value}')

        if isinstance(value, int):
            return value

        if value.isnumeric():
            return int(value)
        else:
            raise ExecException(f'Variable {variablename} has not a numeric value: {value}')

    @staticmethod
    def variable_to_bool(variablename: str, value: str) -> bool:
        if str(value).lower() in ('yes', 'y', 'true', 't', '1'):
            return True
        if str(value).lower() in ('no', 'n', 'false', 'f', '0', '0.0', '', 'none', '[]', '{}'):
            return False
        raise ExecException(f'Invalid value for boolean conversion of {variablename}: {value}')
