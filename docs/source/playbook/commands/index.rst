.. _commands:

========
Commands
========

The *'commands-section'* holds a list of AttackMate-commands that are executed sequentially from
top to bottom.

Every command, regardless of the type has the following general options:

.. confval:: cmd

   *cmd* defines the command that should be executed. The purpose of this option varies depending on the type of command.

   :type: str

.. confval:: save

   Save the output of the command to a file.

   :type: str

   .. code-block:: yaml

      commands:
        - type: shell
          cmd: nmap localhost
          save: /tmp/nmap_localhost.txt

.. confval:: exit_on_error

   If this option is true, attackmate will exit with an error if the command returns with a return code
   that is not zero.

   :type: bool
   :default: ``True``

.. confval:: error_if

   If this option is set, an error will be raised if the string was found in the **output**
   of the command.

   :type: str(regex)

   .. code-block:: yaml

      commands:
        # throw an error
        - type: http-client
          cmd: get
          url: https://www.google.com
          error_if: ".*bing.*"


.. confval:: error_if_not

   If this option is set, an error will be raised if the string was not found in the **output**
   of the command.

   :type: str(regex)

   .. code-block:: yaml

      commands:
        # throw an error
        - type: http-client
          cmd: get
          url: https://www.google.com
          error_if_not: ".*bing.*"


.. confval:: loop_if

   If this option is set, the command will be executed again if the string was found in the
   **output** of the command.

   :type: str(regex)

   .. code-block:: yaml

      commands:
        # loop until max-loop-count reached:
        - type: http-client
          cmd: get
          url: https://www.google.com
          loop_if_not: ".*google.*"


.. confval:: loop_if_not

   If this option is set, the command will be executed again if the string was not found in the
   **output** of the command.

   :type: str(regex)

   .. code-block:: yaml

      commands:
        # loop until max-loop-count reached:
        - type: http-client
          cmd: get
          url: https://www.google.com
          loop_if_not: ".*bing.*"

.. confval:: loop_count

   Number of Repetitions if *loop_if* or *loop_if_not* matches.

   :type: ini
   :default: ``3``

.. confval:: only_if

   Execute this command only if the condition is true. The following operators are supported:

   * var1 == var2
   * var1 != var2
   * var1 is var2
   * var1 is not var2
   * var1 < var2
   * var1 <= var2
   * var1 > var2
   * var1 >= var2
   * string !~ pattern
   * string =~ pattern
   * not var
   * var
   * None

   :type: str(condition)

   The =~ operator is used to check if a string matches a regular expression pattern.
   The !~ operator is used to check if a string does not match a regular expression pattern.

   .. code-block:: yaml

      commands:
        - type: shell
          cmd: pgrep mysqld

        - type: regex
          mode: split
          cmd: "\n"
          output:
            KILLPID: $MATCH_0

        # Execute this command only
        # if it is not the init-process
        - type: shell
          cmd: kill $KILLPID
          only_if: $KILLPID > 1

        # Execute this command only if the regex pattern is found
        - type: shell
          cmd: echo "regex match found"
          only_if: some_string =~ some[_]?string


.. confval:: background

   Execute the command as a subprocess in background. If set to *True*,
   the functionality for *error_if* and *error_if_not* as well as printing
   the output is disabled.

   Background-Mode is currently not implemented for the following commands:

   * SSHCommand
   * SFTPCommand
   * MsfModuleCommand
   * IncludeCommand

   :type: bool
   :default: ``False``

   .. note::

      The command in background-mode will not change global variables like
      RESULT_STDOUT or RESULT_CODE.

.. confval:: kill_on_exit

   If this command runs in background-mode, the option *kill_on_exit* controls
   if the main process will wait for this subprocess before exitting or if the
   main process will simply kill the subprocess.

   :type: bool
   :default: ``True``

.. confval:: metadata

   The option *metadata* can be used to pass a dictionary of key value pairs.
   These are not used in command execution but are logged together with the command.

   :type: Dict
   :default: None

   .. code-block:: yaml

      commands:
        - type: debug
          cmd: Come on, Cat
          metadata:
            version: 1
            author: Ellen Ripley


The next pages will describe all possible commands in detail.

.. toctree::
   :maxdepth: 4
   :hidden:

   debug
   father
   httpclient
   include
   json
   loop
   mktemp
   msf-module
   msf-session
   payload
   regex
   setvar
   shell
   sftp
   sleep
   sliver
   sliver-session
   ssh
   vnc
   webserv
