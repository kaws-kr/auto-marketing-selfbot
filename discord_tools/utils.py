import string
import random
import re
import orjson
from base64 import b64encode

from tls_client import Session
from fake_useragent import UserAgent
from user_agents import parse


def genrate_session_id() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def get_user_agent(session: Session) -> str:
    user_agent = UserAgent()
    return user_agent.random


def extract_asset_files(session: Session):
    request = session.get("https://discord.com/login")
    pattern = r'<script\s+src="([^"]+\.js)"\s+defer>\s*</script>'
    matches = re.findall(pattern, request.text)
    return matches



def get_build_number(session: Session) -> int:
    assets = extract_asset_files(session)
    
    build_url = f"https://discord.com{assets[0]}"
    build_response = session.get(build_url)
    build_index = build_response.text.split('build_number:"')[1].split('"')[0]
    
    return int(build_index)


def get_browser_version(user_agent: str) -> str:
    ua = parse(user_agent)
    return ua.browser.version_string

def _handle_metadata(obj):
    return dict(obj)


def _to_json(obj) -> str:
    return orjson.dumps(obj, default=_handle_metadata).decode('utf-8')


def get_info(session: Session) -> tuple[str, str]:
    # try: 
    #     response = session.get("https://cordapi.dolfi.es/api/v2/properties/web")
    #     properties = response.json()

    # except:
    # 포맷이 맞지 않아 일시적으로 사용하지 않음
    user_agent = get_user_agent(session)
    browser_version = get_browser_version(user_agent)
    build_number = get_build_number(session)
    
    properties = {
        'os': 'Windows',
        'browser': 'Chrome',
        'device': '',
        'browser_user_agent': user_agent,
        'browser_version': browser_version,
        'os_version': '10',
        'referrer': '',
        'referring_domain': '',
        'referrer_current': '',
        'referring_domain_current': '',
        'release_channel': 'stable',
        'system_locale': 'en-US',
        'client_build_number': build_number,
        'client_event_source': None,
        'design_id': 0,
    }
        
    json_result = _to_json(properties)
    base64_encoded = b64encode(json_result.encode()).decode("utf-8")
    
    return properties, base64_encoded