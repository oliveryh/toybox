import json
import sqlite3
import subprocess

import click
import requests
from itsdangerous import json
from tqdm import tqdm

# read string from file
with open('token.pwd') as f:
    api_token = f.read().strip()

url = 'https://api.github.com/graphql'
query = '''
query ($owner: String!, $name: String!, $before: String) {
    repository(name: $name, owner: $owner) {
        pullRequests(last:100, before: $before) {
            pageInfo {
                startCursor
                hasNextPage
                endCursor
            }
            nodes {
                author {
                    login
                }
                number
                createdAt
                state
                reviews(last:10, , states: [APPROVED, CHANGES_REQUESTED]) {
                    nodes {
                        author {
                            login
                        }
                        publishedAt
                        state
                    }
                }
            }
        }
    }
    rateLimit {
        limit
        cost
        remaining
        resetAt
    }
}
'''
headers = {'Authorization': 'token %s' % api_token}


@click.command()
@click.option('--owner', prompt='Your Repository Owner')
@click.option('--name', prompt='Your Repository Name')
@click.option('--limit', default=100, help='Number of pull requests to pull')
def run(owner, name, limit):
    """Simple program that greets NAME for a total of COUNT times."""

    ctx = click.get_current_context()
    ctx.meta['OWNER'] = owner
    ctx.meta['NAME'] = name
    ctx.meta['LIMIT'] = limit // 100
    ctx.meta['BEFORE'] = None

    pull_data()
    generate_db()
    converting_to_cytoscape()
    display_graph()


def pull_data():

    with open('output.jsonl', 'w') as outfile:
        for entry in paginate_reverse():
            json.dump(entry, outfile)
            outfile.write('\n')


def paginate_reverse():

    ctx = click.get_current_context()
    owner = ctx.meta['OWNER']
    name = ctx.meta['NAME']
    before = ctx.meta['BEFORE']
    limit = ctx.meta['LIMIT']
    variables = {
        'owner': owner,
        'name': name,
        'before': before,
    }

    print(f"ℹ️  - Requesting Data | owner: {owner} | name: {name}")

    for _ in tqdm(range(limit)):
        payload = requests.post(
            url, json={'query': query, 'variables': variables}, headers=headers
        ).json()
        if 'errors' in payload:
            for error in payload['errors']:
                print(f'❌ - Errors found in payload: {error["message"]}')
            return
        remaining_credits = payload['data']['rateLimit']['remaining']
        start_cursor = payload['data']['repository']['pullRequests']['pageInfo'][
            'startCursor'
        ]
        variables.update(
            {
                'before': start_cursor,
            }
        )
        if remaining_credits == 0:
            break
        yield from get_pull_requests(payload)

    print(f"ℹ️  - You have {remaining_credits} credits left")
    print('✅ - Data generated')


def get_reviews(pull_request):
    for review in pull_request['reviews']['nodes']:
        try:
            review_author = review['author']['login']
        except TypeError:
            review_author = None
        review_published_at = review['publishedAt']
        review_state = review['state']
        yield {
            'review_author': review_author,
            'review_published_at': review_published_at,
            'review_state': review_state,
        }


def get_pull_requests(payload):
    for pull_request in payload['data']['repository']['pullRequests']['nodes']:
        pr_number = pull_request['number']
        try:
            pr_author = pull_request['author']['login']
        except TypeError:
            pr_author = None
        except KeyError:
            pr_author = None
        pr_created_at = pull_request['createdAt']
        pr_state = pull_request['state']
        for review in get_reviews(pull_request):
            yield {
                'pr_author': pr_author,
                'pr_number': pr_number,
                'pr_created_at': pr_created_at,
                'pr_state': pr_state,
                **review,
            }


def generate_db():

    try:
        subprocess.check_call(
            'sqlite-utils insert github.db reviews output.jsonl --nl', shell=True
        )
        subprocess.check_call(
            'sqlite-utils extract github.db reviews pr_author pr_number pr_created_at pr_state --table pull_requests',
            shell=True,
        )
    except subprocess.CalledProcessError:
        print('❌ - Error generating database')
        return
    print('✅ - Database generated')


def get_reviews_from_db(json_str=False):
    conn = sqlite3.connect('github.db')
    conn.row_factory = (
        sqlite3.Row
    )  # This enables column access by name: row['column_name']
    db = conn.cursor()

    rows = db.execute(
        '''
    SELECT
        pr_author AS target,
        review_author AS source,
        SUM(CASE WHEN review_state = "APPROVED" THEN 1 ELSE 0 END) AS value,
        CAST(SUM(CASE WHEN review_state = "CHANGES_REQUESTED" THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) AS change_request_rate,
        "licensing" AS type
    FROM
        reviews AS r
            LEFT JOIN
        pull_requests AS p
    ON
        p.id = r.pull_requests_id
    WHERE
        review_author <> pr_author
        AND
        review_state IN ("CHANGES_REQUESTED", "APPROVED")
    GROUP BY
        review_author, pr_author
    HAVING
        value > 1
    '''
    ).fetchall()

    conn.commit()
    conn.close()

    if json_str:
        return json.dumps([dict(ix) for ix in rows])  # CREATE JSON

    return [dict(ix) for ix in rows]  # CREATE LIST


def get_node_to_id_mapping(connections):
    return {
        node_name: str(idx)
        for idx, node_name in enumerate(
            set(x['source'] for x in connections).union(
                set(x['target'] for x in connections)
            )
        )
    }


def filter_connections(connections):
    return [connection for connection in connections if connection["value"] > 5]


def convert_cytoscape(connections):

    node_to_id_mapping = get_node_to_id_mapping(connections)

    return {
        "nodes": [
            {"data": {"id": v, "name": k}} for k, v in node_to_id_mapping.items()
        ],
        "edges": [
            {
                "data": {
                    "source": node_to_id_mapping[connection["source"]],
                    "target": node_to_id_mapping[connection["target"]],
                    "value": connection["value"],
                    "change_request_rate": connection["change_request_rate"],
                }
            }
            for connection in connections
        ],
    }


def converting_to_cytoscape():

    with open('connections.json', mode='w') as f:
        connections = get_reviews_from_db()
        connections = filter_connections(connections)
        f.write(json.dumps(convert_cytoscape(connections)))
    print('✅ - Prepared connections from frontend')


def display_graph():

    print('🌐 - Serving on http://localhost:8080')
    # start http server at port 8080
    from http.server import HTTPServer, SimpleHTTPRequestHandler

    HTTPServer(('', 8080), SimpleHTTPRequestHandler).serve_forever()


if __name__ == '__main__':
    run()
