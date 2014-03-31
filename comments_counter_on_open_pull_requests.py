from collections import defaultdict

__author__ = 'omert'

import requests
import json
import getpass

user = raw_input('Please enter your github username: ')
password = getpass.getpass('Please provide your password to github: ')
BASE_URL = 'https://api.github.com/repos/kenshoo'
AUTH_TUPLE = (user, password)


def get_response(url, params={}):
    return requests.get(url, auth=AUTH_TUPLE, params=params)


def get_dict(url):
    r = get_response(url)
    return json.loads(r.text)


def get_list_from_response(resp):
    l = json.loads(resp.text)
    if not resp.links.get('next', None):
        return l
    return l + get_list_from_response(requests.get(resp.links['next']['url'], auth=AUTH_TUPLE))


def get_pulls_from_repo(repo_url):
    return get_list_from_response(get_response(repo_url + '/pulls'))


def get_commenters_hist_per_repo(comments_per_repo):
    commenters_per_repo = {}
    for repo, comments in comments_per_repo.iteritems():
        commenters_per_repo[repo] = defaultdict(lambda: 0)
        for comment in comments:
            commenter = comment['user']['login']
            commenters_per_repo[repo][commenter] += 1
    return commenters_per_repo


def get_comments_per_user(summerized_per_repo):
    comments_per_user = {}
    for repo, commenters_hist in summerized_per_repo.iteritems():
        reversed = dict([(commenter, comments + 4) for (commenter, comments) in commenters_hist.iteritems()])
        for commenter, times in reversed.iteritems():
            try:
                comments_per_user[commenter] += times
            except KeyError:
                comments_per_user[commenter] = times
    return comments_per_user


def summerize(commenters_hist_per_repo):
    summerized_per_repo = dict([x for x in commenters_hist_per_repo.iteritems() if x[1]])
    return get_comments_per_user(summerized_per_repo)


def get_comments_per_repo(non_empty_pulls_per_repo):
    comments_per_repo = defaultdict(list)
    for repo_name, pulls_list in non_empty_pulls_per_repo.items():
        comments_per_repo[repo_name] = reduce(lambda a, b: a+b,
                                              [get_list_from_response(get_response(pull['review_comments_url'])) for pull in pulls_list],
                                              [])
    return comments_per_repo

repositories = get_list_from_response(get_response('https://api.github.com/orgs/kenshoo/repos'))
non_empty_pulls_per_repo = dict([(repo['name'], get_pulls_from_repo(repo['url'])) for repo in repositories if repo])
comments_per_repo = get_comments_per_repo(non_empty_pulls_per_repo)
commenters_hist_per_repo = get_commenters_hist_per_repo(comments_per_repo)
summary = summerize(commenters_hist_per_repo)
for commenter, points in sorted(summary.iteritems(), key=lambda x: x[1], reverse=True)[:10]:
    print commenter, points