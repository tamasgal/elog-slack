#!/usr/bin/env python
"""

Slackbot for ELOG

"""
import os
import re

import pyinotify

from pyslack import SlackClient


wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE

URL = 'http://elog.whatever.com'
LOGBOOK_PATH = '/usr/local/elog/logbooks'
BOTNAME = 'ELOG'
PREVIEW_LENGTH = 150
FALLBACK_DESTINATION = '#elog'
DESTINATIONS = {
    'Analysis': '#analysis',
    'Computing and Software': '#software',
    'Whatever': '@tgal',
    }

slack = SlackClient('YOUR-SLACK-API-TOKEN')


class ElogEntry(object):
    def __init__(self, logbook, msg_id=None):
        self.logbook = logbook
        self.id = msg_id
        self.header = {}
        self.content = ''

    @property
    def author(self):
        return self._lookup('Author')

    @property
    def type(self):
        return self._lookup('Type')

    @property
    def subject(self):
        return self._lookup('Subject')

    @property
    def url(self):
        escaped = re.sub(r"[\s_]+", '+', self.logbook)
        return URL + '/' + escaped + '/' + str(self.id)

    def _lookup(self, key):
        try:
            return self.header[key]
        except KeyError:
            return "Unknown"

    def __repr__(self):
        return ("ELOG entry from *{0.author}* in *{0.logbook}* (_{0.type}_):\n"
                "*{0.subject}*\n{1}...\n<{0.url}>"
                .format(self, self.content[:PREVIEW_LENGTH]))


class ElogEntryBundle(object):
    def __init__(self, pathname):
        self.logbook = dirname(pathname)

        with open(pathname) as input_file:
            self.entries = self._parse_entries(input_file)

    @property
    def newest_entry(self):
        return self.entries[-1]

    def _parse_entries(self, input_file, msg_id=None):
        if msg_id is None:
            line = input_file.readline()
            if not line.startswith('$@MID@$:'):
                raise ValueError("Not an ELOG-entry file!")
            msg_id = int(line.split(':')[1])

        entry = ElogEntry(self.logbook, msg_id)
        for line in input_file:
            if line.startswith(40*'='):
                break
            parameter, value = re.findall(r'([^:.]*): (.*)', line)[0]
            entry.header[parameter] = value
        for line in input_file:
            if line.startswith('$@MID@$:'):
                msg_id = int(line.split(':')[1])
                return [entry] + self._parse_entries(input_file, msg_id)
            else:
                entry.content += line
        return [entry]


class EventHandler(pyinotify.ProcessEvent):
    def my_init(self):
        self.logged_files = []

    def process_IN_CLOSE_WRITE(self, event):
        if not self._is_valid_filetype(event.pathname):
            return

        try:
            elog_bundle = ElogEntryBundle(event.pathname)
            elog_entry = elog_bundle.newest_entry
        except ValueError:
            print("Could not parse '{0}'. Ignoring...".format(event.pathname))
            return

        try:
            destination = DESTINATIONS[elog_entry.logbook]
        except KeyError:
            print("No destination for logbook '{0}'. Using fallback..."
                  .format(elog_entry.logbook))
            destination = FALLBACK_DESTINATION
        finally:
            if event.name in self.logged_files:
                pre = 'Updated '
            else:
                pre = ''
                self.logged_files.append(event.name)
            message = pre + str(elog_entry)
            print(message)
            slack.chat_post_message(destination, message, username=BOTNAME)

    def _is_valid_filetype(self, path):
        return path.endswith('.log')


def dirname(filepath):
    return os.path.basename(os.path.dirname(filepath))


handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(LOGBOOK_PATH, mask, rec=True)

notifier.loop()
