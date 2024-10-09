import time
from urllib.parse import quote
from typing import TYPE_CHECKING, Literal, Union, Any, Sequence

from tls_client.sessions import Session
from tls_client.response import Response

from .errors import (
    HTTPException,
    RateLimited,
    Forbidden,
    NotFound,
    LoginFailure,
    DiscordServerError,
    GatewayNotFound,
    CaptchaRequired
)
from .utils import get_info, _to_json, genrate_session_id
from .handler import CaptchaHandler
from .types.snowflake import Snowflake


INTERNAL_API_VERSION = 9


def json_or_text(response: Response) -> Union[dict[str, Any], str]:
    if response.headers.get("Content-Type")  == 'application/json':
        return response.json()
    else:
        print(response.text)
        return response.text


class Route:
    BASE = f"https://discord.com/api/v{INTERNAL_API_VERSION}"

    def __init__(self, method: str, path: str, **parameters):
        self.path = path
        self.method = method
        
        url = self.BASE + path
        if parameters:
            url = url.format_map(
                {k: quote(v) if isinstance(v, str) else v for k, v in parameters.items()}
            )
        self.url = url



class HTTPClient:
    def __init__(self, token: str, proxy: str | None = None, captcha_handler: CaptchaHandler | None = None):
        self.session = Session(random_tls_extension_order=True)
        self.token = token
        self.proxy = proxy
        self.captcha_handler = captcha_handler
        
        self.super_properties, self.encoded_super_properties = get_info(self.session)


    def __del__(self):
        self.session.close()


    @property
    def browser_version(self) -> str:
        return self.super_properties["browser_version"]


    @property
    def user_agent(self) -> str:
        return self.super_properties['browser_user_agent']


    @property
    def fingerprint(self) -> str:
        response = self.session.get("https://discord.com/api/v9/experiments")
        data = response.json()
        
        return data["fingerprint"]


    def request(self, route: Route, **kwargs):
        method = route.method
        url = route.url

        headers = {
            "Authorization": self.token,
            'Accept-Language': 'en-US',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://discord.com',
            'Pragma': 'no-cache',
            'Referer': 'https://discord.com/channels/@me',
            # 'Sec-CH-UA': '"Google Chrome";v="{0}", "Chromium";v="{0}", ";Not A Brand";v="99"'.format(
            #     self.browser_version.split('.')[0]
            # ),
            # 'Sec-CH-UA-Mobile': '?0',
            # 'Sec-CH-UA-Platform': '"Windows"',
            # 'Sec-Fetch-Dest': 'empty',
            # 'Sec-Fetch-Mode': 'cors',
            # 'Sec-Fetch-Site': 'same-origin',
            'User-Agent': self.user_agent,
            'X-Discord-Locale': 'en-US',
            'X-Debug-Options': 'bugReporterEnabled',
            'X-Super-Properties': self.encoded_super_properties,
            # 'X-Track': 'eyJvcyI6IklPUyIsImJyb3dzZXIiOiJTYWZlIiwic3lzdGVtX2xvY2FsZSI6ImVuLUdCIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKElQaG9uZTsgQ1BVIEludGVybmFsIFByb2R1Y3RzIFN0b3JlLCBhcHBsaWNhdGlvbi8yMDUuMS4xNSAoS0hUTUwpIFZlcnNpb24vMTUuMCBNb2JpbGUvMTVFMjQ4IFNhZmFyaS82MDQuMSIsImJyb3dzZXJfdmVyc2lvbiI6IjE1LjAiLCJvc192IjoiIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfZG9tYWluX2Nvb2tpZSI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjk5OTksImNsaWVudF9ldmVudF9zb3VyY2UiOiJzdGFibGUiLCJjbGllbnRfZXZlbnRfc291cmNlIjoic3RhYmxlIn0',
        }

        payload = kwargs.pop("json", None)
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            kwargs["data"] = _to_json(payload)

        kwargs["headers"] = headers
        
        if self.proxy is not None:
            kwargs["proxy"] = self.proxy

        for tries in range(5):
            try:
                response = self.session.execute_request(method, url, **kwargs)
                data = json_or_text(response)
                status_code = response.status_code
                
                if 200 <= status_code < 300:
                    return data
                
                if status_code == 429:
                    if not response.headers.get("Via") or isinstance(data, str):
                        raise HTTPClient(response, data)
                    
                    retry_after: float = data["retry_after"]
                    raise RateLimited(retry_after)
                
                # 무조건 재시도
                if status_code in {500, 502, 504, 507, 522, 523, 524}:
                    time.sleep(1 + tries * 2)
                
                if status_code == 403:
                    raise Forbidden(response, data)
                elif status_code == 404:
                    raise NotFound(response, data)
                elif status_code >= 500:
                    raise DiscordServerError(response, data)
                else:
                    if "captcha_key" in data:
                        raise CaptchaRequired(response, data)
                    raise HTTPException(response, data)
            
            except CaptchaRequired as e:
                if tries == 4:
                    raise
                else:
                    previous = payload
                    previous["captcha_key"] = self.captcha_handler.solve_hcatpcha(data["captcha_sitekey"], data["captcha_rqdata"], self.proxy)
                    previous["captcha_rqtoken"] = data["captcha_rqtoken"]
                    
                    kwargs["data"] = _to_json(previous)
            
            except RateLimited as e:
                time.sleep(e.retry_after)
            
            except:
                raise
                

    def accept_invite(self, invite: str):
        data = self.request(
            Route("POST", "/invites/{invite}", invite=invite), 
            headers={"x-fingerprint": self.fingerprint},
            json={"session_id": genrate_session_id()}
        )
        
        return data


    def get_guild_subscription_slots(self):
        return self.request(Route("GET", "/users/@me/guilds/premium/subscription-slots"))


    def get_subscriptions(self, limit: None | int = None, include_inactive: bool = False):
        params = {}
        if limit:
            params["limit"] = limit
        if include_inactive:
            params["include_inactive"] = "true"

        return self.request(Route("GET", "/users/@me/billing/subscriptions"), params=params)


    def get_subscription(self, subscription_id: int):
        return self.request(
            Route('GET', '/users/@me/billing/subscriptions/{subscription_id}', subscription_id=subscription_id)
        )


    def change_hypesquad(self, house_id: Literal[1, 2, 3]):
        payload = {"house_id": house_id}
        # 1: Bravery | 2: Brilliance | 3: Balance
        
        return self.request(Route("POST", "/hypesquad/online"), json=payload)


    def add_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str) -> None:
        route = Route(
            "PUT",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        
        return self.request(route)


    def remove_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str, member_id: Snowflake):
        route = Route(
            "DELETE",
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{member_id}',
            channel_id=channel_id,
            message_id=message_id,
            member_id=member_id,
            emoji=emoji
        )
        
        return self.request(route)


    def remove_own_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str):
        route = Route(
            "DELETE",
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        
        return self.request(route)


    def get_reaction_users(self, channel_id: Snowflake, message_id: Snowflake, emoji: str, limit: int, after: int | None = None):
        route = Route(
            "GET",
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji
        )
        
        params = {
            "limit": limit
        }
        if after is not None:
            params["after"] = after
        
        return self.request(route, params=params)


    def clear_reactions(self, channel_id: Snowflake, message_id: Snowflake):
        route = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions',
            channel_id=channel_id,
            message_id=message_id
        )
        
        return self.request(route)


    def clear_single_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str):
        route = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )

        return self.request(route)


    def apply_guild_subscription_slots(self, guild_id: Snowflake, slot_ids: Sequence[Snowflake]):
        payload = {"user_premium_guild_subscription_slot_ids": slot_ids}
        
        return self.request(Route("PUT", "/guilds/{guild_id}/premium/subscriptions", guild_id=guild_id), json=payload)
