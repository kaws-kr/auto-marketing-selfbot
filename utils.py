import re
from unicodedata import east_asian_width


def extract_discord_invites(text: str) -> list[str]:
    invite_pattern = r"(https?://discord\.gg/[a-zA-Z0-9]+)"
    invites = re.findall(invite_pattern, text)
    return invites

def get_display_width(text) -> int:
    return sum(2 if east_asian_width(char) in ('F', 'W', 'A') else 1 for char in text)

def adjust_to_width(text, target_width, align='left'):
    current_width = get_display_width(text)
    padding = target_width - current_width
    
    if padding <= 0:
        return text  # 이미 목표 너비 이상일 경우 그대로 반환
    
    if align == 'left':
        return text + ' ' * padding
    elif align == 'right':
        return ' ' * padding + text
    elif align == 'center':
        left_padding = padding // 2
        right_padding = padding - left_padding
        return ' ' * left_padding + text + ' ' * right_padding