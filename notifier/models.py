import aiohttp

import notifier


class Telegram(notifier.Notifier):
    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token

    async def notify(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'MarkdownV2',
            'disable_web_page_preview': True
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.telegram.org/bot{self.token}/sendMessage', data=payload) as resp:
                if resp.status == 200:
                    print(f'Telegram: {self.chat_id} sent: {text}')
                else:
                    print(f'status: {resp.status}, {resp.reason}\ntext: {text}')
