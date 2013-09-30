import git
from mercurial import ui, hg, cmdutil, match
from collections import defaultdict
import re

def walk_changesets(repo, start, end, path_filter):
    if isinstance(repo, git.Repo):
        paths = [path_filter] if path_filter else []
        for commit in repo.iter_commits(rev='%s..%s' % (end, start), paths=paths):
            yield {'msg': commit.message,
                   'author': '%s <%s>' % (commit.author.name,
                                          commit.author.email)}
    else: 
        pats = () if not path_filter else ['path:%s' % path_filter]
        opts = {'rev': [start + ':' + end]}
        matchfn = match.match(repo.root, repo.getcwd(), pats)
        def prep(ctx, fns):
            pass
        for rev in cmdutil.walkchangerevs(repo, matchfn, opts, prep):
            yield {'msg': rev.description(),
                   'author': str(rev.user()).decode('utf-8')}

def collect_authors_between_revisions(start, end, repo_path, path_filter=None):
    try:
        repo = hg.repository(ui.ui(), repo_path)
    except:
        try:
            repo = git.Repo(repo_path)
            assert repo.bare == False
        except:
            raise '%s is not an hg or git clone' % repo_path

    authors = defaultdict(int)

    merge_regex = re.compile('[Mm]erge (.*) (in|to) (.*)')
    backout_regex = re.compile('[Bb]ack(ed)*(\s*)out')
    for rev in walk_changesets(repo, start, end, path_filter):
        message = rev['msg']
        if backout_regex.match(message) or merge_regex.match(message):
            continue

        authors[rev['author']] += 1

    return authors

def classify_authors(authors, emails_path):
    with open(emails_path) as f:
        lines = filter(lambda x: x.split(), f.readlines())
        emails = map(lambda x: x.split()[0], lines)

    employee_authors = set()
    volunteer_authors = set()

    for author in authors:
        for email in emails:
            if email in author:
                employee_authors.add(author)
                break
        else:
            # Last ditch. I feel bad.
            if '@mozilla.org' in author or '@mozilla.com' in author:
                employee_authors.add(author)
            else:
                volunteer_authors.add(author)

    return (employee_authors, volunteer_authors)
