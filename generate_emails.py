import json
import re
import urllib2
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--user", dest="user", help="LDAP username")
parser.add_option("-p", "--pass", dest="passwd", help="LDAP password")
(options, args) = parser.parse_args()

def search_for_string(s, user, passwd):
    # Create an OpenerDirector with support for Basic HTTP Authentication...
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='LDAP - Valid User Required',
                              uri='https://phonebook.mozilla.org/',
                              user=user,
                              passwd=passwd)
    opener = urllib2.build_opener(auth_handler)
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)
    try:
        return urllib2.urlopen('https://phonebook.mozilla.org/search.php?query=%s&format=json' % s)
    except urllib2.HTTPError, e:
        print e
        print e.headers
        return ''

emails = set()
for search in ['a','e','i','o','u']:
    data = json.load(search_for_string(search, options.user, options.passwd))
    for result in data:
        if 'mail' in result:
            emails.add(result['mail'])
        if 'emailalias' in result:
            aliases = result['emailalias']
            if not isinstance(aliases, list):
                aliases = [aliases]
            for email in aliases:
                if email:
                    emails.add(email.split()[0])
        if 'bugzillaemail' in result:
            emails.add(result['bugzillaemail'])

for email in emails:
    print email
