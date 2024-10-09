from .http import HTTPClient
from .handler import CaptchaHandler


class Client:
    def __init__(self, token: str, proxy: str | None = None, captcha_handler: CaptchaHandler | None = None):
        self.token = token
        self.proxy = proxy
        self.captcha_handler = captcha_handler
        
        self.http_client = HTTPClient(
            self.token,
            self.proxy,
            self.captcha_handler
        )


    def join_guild(self, invite: str):
        data = self.http_client.join_guild(invite)
        return None


    def premium_guild_subscription_slots(self):
        data = self.http_client.get_guild_subscription_slots()
        
        return [d for d in data]


    def subscriptions(self, limit: int | None = None, with_inactive: bool = False):
        data = self.http_client.get_subscriptions(limit=limit, include_inactive=with_inactive)
        
        return [d for d in data]


    def add_reaction(self, channel_id: int, message_id: int, emoji: str):
        self.http_client.add_reaction(channel_id, message_id, emoji)
        