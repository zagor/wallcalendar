import json
from requests import get

from config import Config


def get_history(entities: list[str]):
    config = Config().get("HomeAssistant")
    entity_filter = 'filter_entity_id=' + ','.join(entities)
    args = '?minimal_response&no_attributes&significant_changes_only&' + entity_filter
    url = config['base_url'] + '/api/history/period' + args
    headers = {
        'Authorization': f'Bearer {config["access_token"]}',
        'content-type': 'application/json',
    }
    response = get(url, headers=headers)
    if response.status_code != 200:
        print(f'http error {response.status_code}')
        return
    return json.loads(response.text)
