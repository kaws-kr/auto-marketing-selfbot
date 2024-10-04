import logging

import config
from auto_marketing_selfbot.bot import SelfMarketingBot


if __name__ == "__main__":
    bot = SelfMarketingBot(
        marketing_message=config.MESSAGE,
        auto_reply_message=config.AUTO_REPLY_MESSAGE,
        max_ratelimit_timeout=0.1
    )
    bot.run(config.TOKEN, log_level=logging.ERROR)
