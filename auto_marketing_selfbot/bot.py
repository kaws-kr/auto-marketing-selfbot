from datetime import datetime

import discord
from discord.ext import tasks
from colorama import Fore, Style

import config
from auto_marketing_selfbot.utils import get_display_width, adjust_to_width


class SelfMarketingBot(discord.Client):
    """
    마케팅 및 자동 응답 기능을 제공하는 디스코드 클라이언트 봇.

    이 봇은 특정 키워드에 기반한 채널에 마케팅 메시지를 자동으로 전송하고,
    DM(다이렉트 메시지)에 대해 미리 설정된 자동 응답 메시지를 보냅니다.

    Args:
        marketing_message (str): 채널에 보낼 마케팅 메시지.
        auto_reply_message (str): DM에 대한 자동 응답 메시지.
        **options: discord.Client 클래스에 전달할 추가 옵션.
    """

    def __init__(self, marketing_message: str, auto_reply_message: str, **options):
        """
        SelfMarketingBot의 생성자.

        마케팅 메시지와 자동 응답 메시지를 설정하고,
        디스코드 클라이언트의 옵션을 설정합니다.

        Args:
            marketing_message (str): 마케팅 메시지.
            auto_reply_message (str): 자동 응답 메시지.
            **options: 추가적인 디스코드 클라이언트 옵션.
        """
        super().__init__(**options)

        self.marketing_message = marketing_message
        self.auto_reply_message = auto_reply_message


    async def on_ready(self) -> None:
        """
        봇이 준비되었을 때 호출되는 메서드.

        봇의 사용자 정보와 가입된 서버 정보를 출력합니다.
        """
        print("========================================")
        print(f"Name: {self.user.name}")
        print(f"Created at {self.user.created_at.strftime('%Y-%m-%d %H:%M:%S')} ({discord.utils.utcnow() - self.user.created_at})")
        print(f"Email {self.user.email}")
        print(f"Phone {self.user.phone}")
        print(f"Nitro: {self.user.premium_type}")
        print(f"Guild Count {len(self.guilds):,}")
        print(f"Friend Count {len(self.friends):,}")
        print(f"Required action {self.required_action}")
        print("========================================")

        await self.send_message.start()


    async def on_relationship_add(self, relationship: discord.Relationship):
        """
        새로운 관계(친구 추가 등)가 생겼을 때 호출되는 메서드.

        Args:
            relationship (discord.Relationship): 새로 추가된 관계 객체.
        """
        await relationship.accept()
        await relationship.user.create_dm(self.auto_reply_message)


    async def on_message(self, message: discord.Message):
        """
        메시지를 받을 때 호출되는 메서드.

        Args:
            message (discord.Message): 수신된 메시지 객체.
        """
        if message.author == self.user:
            return

        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send(self.auto_reply_message)


    async def get_channel_for_keywords(self, keywords: list[str]) -> list[discord.TextChannel]:
        """
        주어진 키워드를 이름에 포함하는 채널을 검색하는 메서드.

        Args:
            keywords (list[str]): 채널 이름에서 검색할 키워드 리스트.

        Returns:
            list[discord.TextChannel]: 검색된 텍스트 채널 리스트.
        """
        channels = [
            channel
            for guild in self.guilds
            for channel in guild.text_channels
            if any(
                keyword in channel.name
                for keyword in keywords
            )
        ]

        return channels

    @tasks.loop(minutes=config.DELAY)
    async def send_message(self):
        """
        주기적으로 마케팅 메시지를 채널에 전송하는 메서드.

        키워드에 따라 채널을 검색하고, 마케팅 메시지를 해당 채널에 전송합니다.
        """
        keywords = ["당근", "번개", "홍보", "거래", "중고", "장터"]
        channels = await self.get_channel_for_keywords(keywords)

        if not channels:
            print("메세지를 보낼 채널이 존재하지 않습니다, 더 많은 길드에 가입해주세요.")
        else:
            success = 0
            failure = 0

            print(f"{len(channels):,}개의 채널을 찾았습니다.")
            mc = max(get_display_width(channel.name) for channel in channels) + 2
            mg = max(get_display_width(channel.guild.name) for channel in channels) + 2

            for i, channel in enumerate(channels):
                try:
                    await channel.send(content=self.marketing_message)
                except discord.errors.Forbidden as e:
                    result = Fore.RED + e.text
                    failure += 1
                except discord.errors.RateLimited as e:
                    result = Fore.RED + f"Ratelimit: {int(e.retry_after):,}"
                    failure += 1
                except Exception as e:
                    failure += 1
                    raise e
                else:
                    result = Fore.GREEN + "Complete"
                    success += 1

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                time_str = adjust_to_width(now, 22, align='center')
                result_str = adjust_to_width(result, 26, align='center')
                guild_str = adjust_to_width(channel.guild.name, mg, align='center')
                channel_str = adjust_to_width(channel.name, mc, align='left')

                print(f"{Style.RESET_ALL}{i + 1}-{self.send_message.current_loop + 1:,}회 | {Fore.YELLOW}{time_str}{Style.RESET_ALL} | {result_str}{Style.RESET_ALL} | {guild_str} | {channel_str}")

            print(f"{self.send_message.current_loop + 1}회차 실행결과: 성공 {success}  실패 {failure}")

