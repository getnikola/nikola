from nikola.plugin_categories import SignalHandler
from blinker import signal
import logbook
import os

class StdoutHandler(SignalHandler):
    """Logs messages to stderr."""
    name = 'stderr'

    def attach_handler(self, sender):
        """Attach the handler to the logger."""
        conf = self.site.config.get('LOGGING_HANDLERS').get('stderr')
        if conf or os.getenv('NIKOLA_DEBUG'):
            print("stderr handler loaded")

            self.site.loghandlers.append(logbook.StderrHandler(
                level='DEBUG' if os.getenv('NIKOLA_DEBUG') else conf.get('loglevel','WARNING').upper(),
                format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] ### {record.level_name}: {record.channel}: {record.message}'
            ))

    def set_site(self, site):
        self.site = site

        # Plugins are defined in conf.py, so we want to wait for `configured` signal.
        ready = signal('configured')
        ready.connect(self.attach_handler)
