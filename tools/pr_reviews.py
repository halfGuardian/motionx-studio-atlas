#!/usr/bin/env python3
"""Describe GitHub-native review state on the exact PR head; never approve or merge."""
import argparse
import json
from pathlib import Path


def review_state(reviews,head_sha,author):
    latest={}
    for review in sorted(reviews,key=lambda r:(r.get('submitted_at') or '',r.get('id',0))):
        user=review.get('user') or {};login=user.get('login','')
        if login:latest[login]=review
    accepted=[];ignored=[]
    for login,review in latest.items():
        if review.get('state')!='APPROVED':continue
        reason=None
        if review.get('commit_id')!=head_sha:reason='stale_commit'
        elif login==author:reason='PR_author'
        elif review.get('user',{}).get('type')!='User' or login.endswith('[bot]'):reason='bot_or_unknown_account'
        elif review.get('author_association') not in ('OWNER','MEMBER','COLLABORATOR'):reason='not_a_repository_reviewer'
        if reason:ignored.append({'reviewer':login,'reason':reason})
        else:accepted.append({'reviewer':login,'review_id':review.get('id'),'commit_id':head_sha})
    return {'head_sha':head_sha,'recorded_exact_head_account_reviews':accepted,'ignored_approvals':ignored,
            'status':'review_recorded' if accepted else 'pending_review',
            'human_identity_claim':'Account metadata does not prove human intent; a maintainer must personally review and authorise manual merge.',
            'merged':False,'publication_authorised_by_this_tool':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reviews',type=Path,required=True);p.add_argument('--head-sha',required=True);p.add_argument('--author',required=True);a=p.parse_args()
    reviews=json.loads(a.reviews.read_text());reviews=[r for page in reviews for r in page] if reviews and isinstance(reviews[0],list) else reviews
    print(json.dumps(review_state(reviews,a.head_sha,a.author),indent=2))


if __name__=='__main__':main()
