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
            self.site.loghandlers.append(logbook.StderrHandler(
                level='DEBUG' if os.getenv('NIKOLA_DEBUG') else conf.get('loglevel','WARNING').upper(),
                format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
            ))

    def set_site(self, site):
        self.site = site

        ready = signal('sighandlers_loaded')
        ready.connect(self.attach_handler)
