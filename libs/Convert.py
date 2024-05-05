from typing import Optional
from discord import Asset


def icon_convert(icon: Optional[Asset]) -> str:
    if not icon:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    else:
        return icon.replace(format='png').url
