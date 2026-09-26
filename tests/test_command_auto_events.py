"""Read-only filesystem activity must not cause live-reload feedback loops."""

import asyncio
from types import SimpleNamespace

import pytest

from nikola.plugins.command.auto import CommandAuto, NikolaEventHandler

watchdog_events = pytest.importorskip('watchdog.events')
if not hasattr(watchdog_events, 'FileClosedNoWriteEvent'):
    pytest.skip('Watchdog does not provide read-only close events', allow_module_level=True)
from watchdog.events import (  # noqa: E402
    FileClosedEvent, FileClosedNoWriteEvent, FileModifiedEvent, FileOpenedEvent,
)


@pytest.mark.parametrize('event_class,expected', [
    (FileOpenedEvent, []),
    (FileClosedEvent, []),
    (FileClosedNoWriteEvent, []),
    (FileModifiedEvent, ['index.html']),
])
def test_output_read_events_do_not_queue_reload(tmp_path, event_class, expected):
    """Dispatch real Watchdog events through the actual output reload handler."""
    async def run():
        command = CommandAuto()
        command.site = SimpleNamespace(config={'OUTPUT_FOLDER': str(tmp_path)})
        command.reload_queue = asyncio.Queue()
        handler = NikolaEventHandler(command.reload_page, asyncio.get_running_loop())
        handler.dispatch(event_class(str(tmp_path / 'index.html')))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        queued = []
        while not command.reload_queue.empty():
            queued.append(command.reload_queue.get_nowait())
        assert queued == expected

    asyncio.run(run())
