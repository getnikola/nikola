from nikola.plugin_categories import SignalHandler
from blinker import signal
import logbook

class SmtpHandler(SignalHandler):
    name = 'smtp'

    def attach_handler(self, sender):
        """Add the handler to a list of handlers that are attached when get_logger() is called.."""
        smtpconf = self.site.config.get('LOGGING_HANDLERS').get('smtp')
        if smtpconf:
            print("loaded smtp handler")

            smtpconf['format_string'] = u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
            self.site.loghandlers.append(logbook.MailHandler(
                smtpconf.pop('from_addr'),
                smtpconf.pop('recipients'),
                **smtpconf 
            ))

    def set_site(self, site):
        self.site = site

        # Plugins are defined in conf.py, so we want to wait for `configured` signal.
        ready = signal('configured')
        ready.connect(self.attach_handler)
