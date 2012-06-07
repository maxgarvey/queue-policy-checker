"""A super minimal RT search client and parser for PSU Account reset requests"""

import logging
import requests

def search(query, credentials, url):
    """Query RT via the API.
    query: the RTQL query
    credentials: a user, pass dict
    url: base RT url"""
    url = "{}/search/ticket".format(url)
    query_string = {'query': query, 'orderby': '-Created', 'format': 's'}
    response = requests.post(url, data=credentials, params=query_string)
    if response.ok:
        return parse_search(response.text)
    else:
        raise Exception("RT: Search Failed")

def parse_search(response):
    """Parse RT search results for account reset requests.
    response: an RT API response"""
    message = split_response(response)
    for req in message:
        # the ticket id is the first chunk before ': '
        splitreq = req.split(': ')
        ticket = splitreq[0]
        subject = ": ".join(splitreq[1:])
        logging.debug("RT: Yielding ticket=%s and subject='%s'", ticket, subject)
        yield (ticket, subject)

def split_response(rt_response):
    """RT sends it's own 'status' in addition to content.
       This function returns the message and raises an exception on failure"""
    response = rt_response.split('\n')
    # This is the RT request status, not HTTP status per se
    if '200 Ok' in response[0]:
        # we skip the first and last lines in response as they're ''
        message = response[2:-1]        # it may be possible to do [2:-2] here
        logging.info("RT: response='%s'", message)
        return message
    else:
        raise Exception("RT: {0}".format(str(response[0])))


def comment(ticket, text, credentials, url):
    """Post a comment to a ticket at the url
       ticket: ticket id
       comment: comment text
       credentials: a user, pass dict
       url: base RT url"""
    url = "{0}/ticket/{1}/comment".format(url, ticket)
    content = "id: {0}\nAction: comment\nText: {1}".format(ticket, text)
    post_data = credentials
    post_data['content'] = content
    response = requests.post(url, data=post_data)
    message = split_response(response.text)
    if 'Message recorded' in message[0]:
        return True
    else:
        return False

def edit(ticket, values, credentials, url):
    """Edit a ticket
       ticket: ticket id
       values: a dict of ticket keys to update with corresponding values
       credentials: a user, pass dict
       url: base RT url"""
    url = "{0}/ticket/{1}/edit".format(url, ticket)
    post_data = credentials
    edits = list()
    for key in values.iterkeys():
        edits.append("{0}: {1}".format(key, values[key]))
    post_data['content'] = "\n".join(edits)
    response = requests.post(url, data=post_data)
    message = split_response(response.text)
    if 'updated' in message[0]:
        return True
    else:
        return False

def move(ticket, queue, credentials, url, unown=True):
    """Move a ticket
       ticket: ticket id
       queue: the new queue for the ticket
       credentials: a user, pass dict
       url: base RT url"""
    values = {"Queue": queue}
    if unown:
        values['Owner'] = "Nobody"
    return edit(ticket, values, credentials, url)

def get(ticket, credentials, url):
    url = "{0}/ticket/{1}".format(url, ticket)
    response = requests.post(url, data=credentials)
    message = split_response(response.text)
    whole_ticket = dict()
    for row in message:
        fields = row.split(': ')
        key = fields.pop(0)
        # replace any later ': ' tokens
        value = ': '.join(fields)
        if key != '':
            whole_ticket[key] = value
    return whole_ticket
