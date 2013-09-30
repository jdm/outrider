import git
from mercurial import ui, hg, cmdutil, match
from collections import defaultdict
import json
import re
import sys

# usage: $0 /path/to/repository newest_rev oldest_rev workday.json emails.txt path_filter

def walk_changesets(repo, start, end, path_filter):
    if isinstance(repo, git.Repo):
        paths = [path_filter] if path_filter else []
        for commit in repo.iter_commits(rev='%s..%s' % (end, start), paths=paths):
            yield {'msg': commit.message,
                   'author': '%s <%s>' % (commit.author.name,
                                          commit.author.email)}
    else: 
        pats = () if not path_filter else ['path:%s' % path_filter]
        opts = {'rev': [to_rev + ':' + from_rev]}
        matchfn = match.match(repo.root, repo.getcwd(), pats)
        def prep(ctx, fns):
            pass
        for rev in cmdutil.walkchangerevs(repo, matchfn, opts, prep):
            yield {'msg': rev.description(),
                   'author': str(rev.user()).decode('utf-8')}

try:
    repo = hg.repository(ui.ui(), sys.argv[1])
except:
    try:
        repo = git.Repo(sys.argv[1])
        assert repo.bare == False
    except:
        print '%s is not an hg or git clone' % sys.argv[1]
        sys.exit(1)

from_rev = sys.argv[2]
to_rev = sys.argv[3]
employees = {}

def sanitize(s):
    return s.replace(u"\u201c", '"').replace(u"\u201d", '"').replace(u"\u2018", "'").replace(u"\u2019", "'") 

with open(sys.argv[4]) as f:
    employees = json.load(f)[u'Report_Entry']
    employees = filter(lambda x: u'primaryWorkEmail' in x, employees)
    emails = map(lambda x: x[u'primaryWorkEmail'], employees)
    names = map(lambda x: (sanitize(x[u'Preferred_Name_-_First_Name']),
                      sanitize(x[u'Preferred_Name_-_Last_Name'])),
                employees)

with open(sys.argv[5]) as f:
    lines = filter(lambda x: x.split(), f.readlines())
    emails += map(lambda x: x.split()[0], lines)

path_filter = None if len(sys.argv) <= 6 else sys.argv[6]

authors = defaultdict(int)

merge_regex = re.compile('[Mm]erge (.*) (in|to) (.*)')
backout_regex = re.compile('[Bb]ack(ed)*(\s*)out')
backouts = 0
merges = 0
for rev in walk_changesets(repo, from_rev, to_rev, path_filter):
    message = rev['msg']
    if backout_regex.match(message):
        backouts += 1
        continue
    if merge_regex.match(message):
        merges += 1
        continue

    authors[rev['author']] += 1

employee_authors = set()
volunteer_authors = set()
partials = set()
for author in authors.keys():
    for (first, last) in names:
        if last in author:
            # Really dumb stemming - if the provided first name matches part of
            # a "word" in the full author's line, claim it's a match (eg. Josh in Joshua)
            if first in author or filter(lambda x: x in first, author.split()):
                employee_authors.add(author)
                try:
                    partials.remove(author)
                except:
                    pass
                break
            else:
                #print 'partial: %s vs %s' % (author, first + " " + last)
                partials.add(author)
    else:
        for email in emails:
            if email in author:
                employee_authors.add(author)
                try:
                    partials.remove(author)
                except:
                    pass
                break
        else:
            # Last ditch. I feel bad.
            if '@mozilla.org' in author or '@mozilla.com' in author:
                try:
                    partials.remove(author)
                except:
                    pass
                employee_authors.add(author)
            else:
                if author in partials:
                    #print 'partial: %s' % author
                    pass
                volunteer_authors.add(author)

print 'Employees: %d' % len(employee_authors)
print 'Volunteers: %d' % len(volunteer_authors)
#print 'Partial matches: %d' % len(partials)
#print partials

emp_contributions = sum(map(lambda x: authors[x], filter(lambda x: x in employee_authors, authors)))
vol_contributions = sum(map(lambda x: authors[x], filter(lambda x: x in volunteer_authors, authors)))

print 'Employee contributions: %d' % emp_contributions
print 'Volunteer contributions: %d' % vol_contributions
sorted_volunteers = sorted(volunteer_authors, key=lambda x: authors[x], reverse=True)
sorted_employees = sorted(employee_authors, key=lambda x: authors[x], reverse=True)
N = 10
top_n_vol = map(lambda x: float(authors[x]), sorted_volunteers[:N])
top_n_emp = map(lambda x: float(authors[x]), sorted_employees[:N])
print 'Contributions from top %d employees: %d' % (N, sum(top_n_emp))
print 'Contributions from top %d volunteers: %d' % (N, sum(top_n_vol))
print 'Top %d volunteers responsible for %f%% of volunteer commits, %f%% overall' % (N, sum(top_n_vol) / vol_contributions * 100, sum(top_n_vol) / (emp_contributions + vol_contributions) * 100)
print 'Top %d employees responsible for %f%% of employee commits, %f%% overall' % (N, sum(top_n_emp) / emp_contributions * 100, sum(top_n_emp) / (emp_contributions + vol_contributions) * 100)

print 'Volunteer commit distribution:'
volunteer_buckets = defaultdict(int)
for author in volunteer_authors:
    volunteer_buckets[authors[author]] += 1
for key in sorted(volunteer_buckets.keys(), reverse=False):
    print '%s: %d' % (key, volunteer_buckets[key])
assert sum(volunteer_buckets.values()) == len(volunteer_authors)

print 'Bucketed volunteer commit distribution:'
buckets = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 10), (10, 20), (20, 2000)]
bucketed = []
for i, (lower, higher) in enumerate(buckets):
    bucketed += [0]
    for subbucket in filter(lambda x: x >= lower and x < higher, volunteer_buckets.keys()):
        bucketed[i] += volunteer_buckets[subbucket]
    print "[%d, %d) - %d" % (lower, higher, bucketed[i])

print 'Skipped %d merges, %d backouts' % (merges, backouts)


print '---'
for author in sorted(volunteer_authors, key=lambda x: authors[x], reverse=True):
    print '%s: %d' % (author, authors[author])
print '---'
for author in sorted(employee_authors, key=lambda x: authors[x], reverse=True):
    print '%s: %d' % (author, authors[author])

    
