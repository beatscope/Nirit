# nirit/utils.py
"""
Common Utilities.

"""
import datetime
import logging
import re
import urllib2
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

logger = logging.getLogger('nirit.utils')


def validate_year(value):
    """
    Validator function:
    * Validates a valid four-digit year.
    * Must be a current or future year.
    """
    year_re = re.compile('^\d{4}$') # Matches any 4-digit number
    # If year does not match our regex
    if not year_re.match(str(value)):
        raise ValidationError(u'{} is not a valid year.'.format(value))
    # Check not after this year
    today = datetime.datetime.now()
    if int(value) > today.year:
        raise ValidationError(u'{} is in the future; please enter a current or past year.'.format(value))


def lookup_email(email):
    """
    Lookup through the Users list for emails with the same TLD.
    When one is found, its Company is returned,
    otherwise, return None.

    We assume the email is valid.

    """
    # Extract TLD
    # format: [nickname]@[tld]
    try:
        tld = email.split('@')[1]
    except IndexError:
        return None
    else:
        # Check whether the TLD belongs to a public domain
        domains = DomainParser().fetch()
        for domain in domains:
            pattern = r'{}'.format(re.escape(domain).replace('\*', '.*'))
            if re.match(pattern, tld) is not None:
                # This TLD belongs to the public domain
                return None
        # If this point is reached, the domain is private
        users = User.objects.filter(email__endswith=tld)\
                            .filter(groups__name__in=['Building Manager', 'Owner', 'Rep', 'Staff'])
        # Users with the same domain are supposed to belong to the same company
        if users:
            try:
                company = users[0].get_profile().company
                return company
            except:
                return None
    return None


class DomainParser(object):
    """
    Uses public repo from SpamAssassin.
    @see: http://svn.apache.org/repos/asf/spamassassin/trunk/rules/20_freemail_domains.cf

    """
    
    def __init__(self):
        url = 'http://svn.apache.org/repos/asf/spamassassin/trunk/rules/20_freemail_domains.cf'
        request = urllib2.Request(url)
        opener = urllib2.build_opener()
        r = opener.open(request)
        self.domain = []
        for line in r.readlines():
            if line.startswith('freemail_domains'):
                domains = line.strip().split(' ')
                domains.pop(domains.index('freemail_domains')) # remove 'freemail_domains'
                self.domain.extend([d for d in domains if d]) # remove empty entries
        r.close()
    
    def fetch(self):
        return self.domain
