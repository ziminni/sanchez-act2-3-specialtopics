"""Replay the exported collection's requests and status/variable assertions."""
import json
from pathlib import Path
import re
from conftest import PASSWORD


def test_postman_collection_in_order(client):
    collection = json.loads(Path('docs/postman_collection.json').read_text())
    variables = {'base_url': '', 'password': PASSWORD, 'run_id': '1234567890123', 'token': ''}
    def substitute(value):
        return re.sub(r'\{\{(\w+)\}\}', lambda match: str(variables[match[1]]), value)
    count = 0
    for folder in collection['item']:
        for item in folder['item']:
            request = item['request']
            headers = {'Content-Type': 'application/json'}
            if request.get('auth', {}).get('type') != 'noauth':
                headers['Authorization'] = 'Bearer ' + variables['token']
            body = substitute(request['body']['raw']) if 'body' in request else None
            response = client.request(request['method'], substitute(request['url']), headers=headers, content=body)
            scripts = item['event'][0]['script']['exec']
            expected = int(re.search(r'to.have.status\((\d+)\)', scripts[0])[1])
            assert response.status_code == expected, f'{folder["name"]} / {item["name"]}: {response.text}'
            for script in scripts[1:]:
                save = re.search(r'collectionVariables.set\("(\w+)", pm.response.json\(\).data.(\w+)\)', script)
                if save:
                    variables[save[1]] = response.json()['data'][save[2]]
            count += 1
    assert count >= 50
