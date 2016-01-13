# elog-slack
This is a very simply slackbot (http://www.slack.com) for the ELOG - Electronic Logbook package by Stefan Ritt (https://midas.psi.ch/elog/).

## Installation

First, create a Slack API token at https://api.slack.com/web (scroll down and click on the green button "Create Token"). The token will be something like `abcd-9522450421-9140563190-18017543932-91348ce321`.

Install Python requirements on your ELOG server

    pip install -r requirements.txt

## Configuriation

Edit the configuration in `elog-slack.py`. The `DESTINATIONS` dictionary is a simple map which connects a slack channel or person to a logbook.

    URL = 'http://elog.whatever.com'
    LOGBOOK_PATH = '/usr/local/elog/logbooks'
    BOTNAME = 'ELOG'
    DESTINATIONS = {
        'Electronics': '#electronics',
        'Analysis': '#analysis',
        'Whatever': '@tgal',
        }
    
    slack = SlackClient('YOUR-SLACK-API-TOKEN')

## Run the `elog-slack`

Here is an example how to run `elog-slack.py` using `nohup` via SSH:

    nohup ./elog-slack.py &

## Example output in Slack

![Screenshot of an elog-slack notification](http://tamasgal.com/km3net/elog-slack.png)
