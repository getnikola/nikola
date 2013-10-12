from nikola.plugin_categories import SignalHandler
from nikola.utils import LOGGER
from blinker import signal
import logbook
import os

class StdoutHandler(SignalHandler):
    name = 'stdout'

    def attach_handler(self, sender):
        """Attach the handler to the logger."""
        if self.site.config.get('LOGGING_HANDLERS').get('stdout') or os.getenv('NIKOLA_DEBUG'):
            print("stdout handler loadded")
            LOGGER.handlers.append(logbook.StderrHandler(
                level='DEBUG' if not os.getenv('NIKOLA_DEBUG') else self.site.config.get('LOGGING_HANDLERS').get('stdout').get('loglevel','WARNING').upper(),
                format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
            ))

    def set_site(self, site):
        self.site = site

        # Plugins are defined in conf.py, so we want to wait for `configured` signal.
        ready = signal('configured')
        ready.connect(self.attach_handler)
