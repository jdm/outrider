from tools import collect_authors_between_revisions, classify_authors
from optparse import OptionParser
import sys

parser = OptionParser()
parser.add_option("-r", "--repo", dest="repo", help="path to git/hg repository")
parser.add_option("-e", "--emails", dest="emails", help="list of emails to categorize as employees")
parser.add_option("-d", "--dir", dest="filter", help="repo subdirectory by which to filter results")

(options, args) = parser.parse_args()
if not options.repo or not options.emails:
    print 'usage: %s --repo path/to/repo --emails path/to/emails' % sys.argv[0]
    sys.exit(1)

with open('ffreleases') as fin:
    releases = map(lambda x: x.strip().split(), fin.readlines())

with open('leverage.csv', 'w') as fout:
    fout.write('"version","employees","volunteers"\n')
    sorted_releases = sorted(releases, key=lambda x: int(x[0]))
    last = sorted_releases[0]
    for release in sorted_releases[1:]:
        authors = collect_authors_between_revisions(start=release[1], end=last[1],
                                                    repo_path=options.repo,
                                                    path_filter=options.filter)
        (employees, volunteers) = classify_authors(authors, options.emails)
        fout.write('%s,%d,%d\n' % (release[0], len(employees), len(volunteers)))
        last = release

