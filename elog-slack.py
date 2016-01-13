#!/usr/bin/env python
"""

Slackbot for ELOG

"""
import os

import pyinotify

from pyslack import SlackClient


wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE

URL = 'http://elog.whatever.com'
LOGBOOK_PATH = '/usr/local/elog/logbooks'
BOTNAME = 'ELOG'
DESTINATIONS = {
    'Operations IT': '@tgal',
    'Operations FR': '@tgal',
    'Qualification': '@tgal',
    'DOM Integration': '@tgal',
    'DU Integration': '@tgal',
    'DAQ Readout': '@tgal',
    'Electronics': '@tgal',
    'Analysis': '@tgal',
    'Computing and Software': '@tgal',
    }

slack = SlackClient('YOUR-SLACK-API-TOKEN')


class EventHandler(pyinotify.ProcessEvent):
    def my_init(self):
        self.logged_files = []

    def process_IN_CLOSE_WRITE(self, event):
        if not self._is_valid_filetype(event.pathname):
            return

        try:
            elog_entry = ElogEntry(event.pathname)
        except ValueError:
            print("Could not parse '{0}'. Ignoring...".format(event.pathname))
            return

        try:
            destination = DESTINATIONS[elog_entry.logbook]
        except KeyError:
            print("No destination for logbook '{0}'. Ignoring..."
                  .format(elog_entry.logbook))
        else:
            if event.name in self.logged_files:
                pre = 'Updated '
            else:
                pre = ''
                self.logged_files.append(event.name)
            message = pre + str(elog_entry)
            slack.chat_post_message(destination, message, username=BOTNAME)

    def _is_valid_filetype(self, path):
        return path.endswith('.log')


class ElogEntry(object):
    def __init__(self, pathname):
        self.logbook = dirname(pathname)
        self.author = None
        self.subject = None
        self.type = None
        self.id = None
        with open(pathname, 'r') as input_file:
            for line in input_file:
                if line.startswith('Author:'):
                    self.author = line.split(':')[1].strip()
                if line.startswith('Subject:'):
                    self.subject = line.split(':')[1].strip()
                if line.startswith('Type:'):
                    self.type = line.split(':')[1].strip()
                if line.startswith('$@MID@$:'):
                    self.id = line.split(':')[1].strip()
        if not all((self.author, self.subject, self.type, self.id)):
            raise ValueError
        self.url = URL + '/' + self.logbook.replace(' ', '+') + '/' + self.id

    def __repr__(self):
        return ("ElogEntry from *{0.author}* in *{0.logbook}* (_{0.type}_):\n"
                "*{0.subject}*\n{0.url}"
                .format(self))


def dirname(filepath):
    return os.path.basename(os.path.dirname(filepath))


handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(LOGBOOK_PATH, mask, rec=True)

notifier.loop()
