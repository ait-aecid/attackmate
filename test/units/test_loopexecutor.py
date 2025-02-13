import logging
import pytest
from attackmate.schemas.playbook import Commands
from attackmate.schemas.debug import DebugCommand
from attackmate.schemas.loop import LoopCommand
from attackmate.schemas.sleep import SleepCommand
from attackmate.executors.common.debugexecutor import DebugExecutor
from attackmate.executors.common.loopexecutor import LoopExecutor
from attackmate.executors.common.sleepexecutor import SleepExecutor
from attackmate.variablestore import VariableStore
from attackmate.processmanager import ProcessManager


@pytest.fixture
def varstore():
    return VariableStore()


@pytest.fixture
def process_manager():
    return ProcessManager()


@pytest.fixture
def sleep_executor(process_manager, varstore):
    return SleepExecutor(process_manager, varstore=varstore)


@pytest.fixture
def debug_executor(process_manager, varstore):
    return DebugExecutor(process_manager, varstore)


@pytest.fixture
def loop_executor(process_manager, varstore, debug_executor, sleep_executor):
    def run_func(commands: Commands):
        for command in commands:
            if command.type == 'debug':
                debug_executor.run(command)
            elif command.type == 'sleep':
                sleep_executor.run(command)
    return LoopExecutor(process_manager, varstore=varstore, runfunc=run_func)


@pytest.fixture
def caplog_setup(caplog):
    caplog.set_level(logging.INFO)
    return caplog



class TestLoopExecutor:

    def test_items(self, caplog_setup, varstore, loop_executor):
        caplog = caplog_setup
        varstore.set_variable('one', ['first', 'second'])
        lc = LoopCommand(
            type='loop', cmd='items($one)', commands=[DebugCommand(cmd='$LOOP_ITEM', type='debug')]
        )
        loop_executor.run(lc)
        assert 'Debug: \'first\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'second\'' in [rec.message for rec in caplog.records]

    def test_range(self, caplog_setup, varstore, loop_executor):
        caplog = caplog_setup
        varstore.set_variable('one', ['first', 'second'])
        lc = LoopCommand(
            type='loop', cmd='range(1,3)', commands=[DebugCommand(cmd='$LOOP_INDEX', type='debug')]
        )
        loop_executor.run(lc)
        assert 'Debug: \'1\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'2\'' in [rec.message for rec in caplog.records]

    def test_break_if_with_range(self, caplog_setup, loop_executor):
        caplog = caplog_setup
        lc = LoopCommand(
            type='loop', cmd='range(1,5)', break_if='$LOOP_INDEX =~ 2', commands=[DebugCommand(cmd='$LOOP_INDEX', type='debug')]
        )
        loop_executor.run(lc)
        assert 'Debug: \'1\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'2\'' not in [rec.message for rec in caplog.records]
        assert 'Debug: \'3\'' not in [rec.message for rec in caplog.records]


    def test_until(self, caplog_setup, loop_executor):
        caplog = caplog_setup
        lc = LoopCommand(
            type='loop',
            cmd='until($LOOP_INDEX == 2)',
            commands=[DebugCommand(cmd='$LOOP_INDEX', type='debug')],
        )
        loop_executor.run(lc)
        # Verify that the loop ran exactly 2 times
        assert 'Debug: \'0\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'1\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'2\'' not in [rec.message for rec in caplog.records]

    def test_range_with_sleep(self, caplog_setup, loop_executor):
        """
        Test that $LOOP_INDEX is substituted correctly for a range-based loop.
        The sleep command ensures substitution works in fields like "seconds," beyond just "cmd".
        """
        caplog = caplog_setup
        lc = LoopCommand(
            type='loop',
            cmd='range(0,3)',
            commands=[
                SleepCommand(type='sleep', cmd='sleep', seconds='$LOOP_INDEX'),
            ],
        )
        loop_executor.run(lc)
        expected_logs = [
            'Sleeping 0 seconds',
            'Sleeping 1 seconds',
            'Sleeping 2 seconds',
        ]
        # Verify the expected log messages
        for log in expected_logs:
            assert log in [rec.message for rec in caplog.records]

    def test_items_with_sleep(self, caplog_setup, varstore, loop_executor):
        """
        Test that $LOOP_ITEM is substituted correctly for a list-based loop.
        The sleep command ensures substitution works in fields like "seconds," beyond just "cmd".
        """
        caplog = caplog_setup
        varstore.set_variable('LISTA', [1, 2])
        lc = LoopCommand(
            type='loop',
            cmd='items(LISTA)',
            commands=[
                SleepCommand(type='sleep', cmd='sleep', seconds='$LOOP_ITEM'),
            ],
        )
        loop_executor.run(lc)
        expected_logs = [
            'Sleeping 1 seconds',
            'Sleeping 2 seconds',
        ]
        # Verify the expected log messages
        for log in expected_logs:
            assert log in [rec.message for rec in caplog.records]
