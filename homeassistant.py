import datetime
import json
import re

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


def get_calendar(calendar: str, first_day: datetime.date, last_day: datetime.date) -> json:
    config = Config().get("HomeAssistant")
    startdate = first_day.isoformat()
    enddate = last_day.isoformat()
    calname = re.sub(r'[^a-z0-9]', '_', calendar.lower())
    args = f'?start={startdate}T00:00:00&end={enddate}T23:59:59'
    url = config['base_url'] + '/api/calendars/calendar.' + calname + args
    headers = {
        'Authorization': f'Bearer {config["access_token"]}',
        'content-type': 'application/json',
    }
    response = get(url, headers=headers)
    if response.status_code != 200:
        print(f'http error {response.status_code}')
        return
    return json.loads(response.text)
