from time import time, mktime
from hashlib import md5
from urllib import urlopen, urlencode
import simplejson as json
import feedparser
import sys

class APIException(Exception): pass

class LastFM(object):
    def __init__(self, username, password):
        self.session = None
        self.nowplaying = None
        self.submission = None
        self.auth(username, password)

    def auth(self, username, password):
        timestamp = str(int(time()))
        authtoken = md5(md5(password).hexdigest() + timestamp).hexdigest()
        params = {
            'hs': 'true',
            'p': '1.2.1',
            'c': 'tst',
            'v': '1.0',
            'u': username,
            't': timestamp,
            'a': authtoken,
        }

        url = 'http://post.audioscrobbler.com/?' + '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        response = urlopen(url)
        lines = response.read().split('\n')

        if lines[0] != 'OK':
            raise APIException('Response not OK: %s' % repr(lines))

        self.session = lines[1]
        self.nowplaying = lines[2]
        self.submission = lines[2]

    def submit(self, title, artist, timestamp, rating=None, source='E'):
        params = {
            's': self.session,
            'a[0]': artist,
            't[0]': title,
            'i[0]': timestamp,
            'o[0]': source,
        }
        if rating:
            params['r[0]'] = rating

        response = urlopen(self.submission, urlencode(params))
        lines = response.read().split('\n')
        if lines[0] != 'OK':
            raise APIException('Response not OK: %s' % repr(lines))

if __name__ == '__main__':
    try:
        submitted = json.load(file('submitted.json', 'r'))
    except:
        submitted = []

    if len(sys.argv) < 4:
        print 'Usage: %s <lastfm username> <lastfm password> <grooveshark username>' % sys.argv[0]
        sys.exit(0)

    lastfm = LastFM(sys.argv[1], sys.argv[2])

    gs = feedparser.parse('http://api.grooveshark.com/feeds/1.0/users/%s/recent_listens.rss' % sys.argv[3])
    entries = gs.entries
    entries.sort(key=lambda x: mktime(x.updated_parsed))
    for track in entries:
        href = track['links'][0]['href']
        playts = mktime(track.updated_parsed)
        if [href, playts] in submitted:
           continue 

        title, artist = track.title.split(' - ', 1)

        lastfm.submit(title, artist, playts)
        print 'Scrobbled', track.title

        submitted.append((href, playts))
        json.dump(submitted, file('submitted.json', 'w'))
