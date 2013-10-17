from nikola.plugin_categories import SignalHandler
from blinker import signal
import logbook

class SmtpHandler(SignalHandler):
    name = 'smtp'

    def attach_handler(self, sender):
        """Add the handler to a list of handlers that are attached when get_logger() is called.."""
        smtpconf = self.site.config.get('LOGGING_HANDLERS').get('smtp')
        if smtpconf:
            smtpconf['format_string'] = '''\
Subject: {record.level_name}: {record.channel}

{record.message}
'''
            self.site.loghandlers.append(logbook.MailHandler(
                smtpconf.pop('from_addr'),
                smtpconf.pop('recipients'),
                **smtpconf 
            ))

    def set_site(self, site):
        self.site = site

        ready = signal('sighandlers_loaded')
        ready.connect(self.attach_handler)
