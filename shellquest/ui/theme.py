"""Theme and styling for ShellQuest UI."""

from rich.style import Style
from rich.theme import Theme as RichTheme


class Theme:
    """Color scheme and styles for ShellQuest."""

    # Color Palette (inspired by modern CLI tools)
    PRIMARY = "#00D9FF"          # Bright cyan
    SECONDARY = "#FF6B9D"        # Pink
    SUCCESS = "#00E676"          # Green
    ERROR = "#FF5252"            # Red
    WARNING = "#FFD740"          # Yellow
    INFO = "#2196F3"             # Blue

    # Text colors
    TEXT_PRIMARY = "white"
    TEXT_SECONDARY = "grey70"
    TEXT_DIM = "grey50"
    TEXT_BRIGHT = "bright_white"

    # Background/Panel colors
    PANEL_BG = "grey15"
    ACCENT_1 = "#667eea"         # Purple
    ACCENT_2 = "#764ba2"         # Deep purple

    # Rarity colors for achievements
    RARITY_COMMON = "grey70"
    RARITY_UNCOMMON = "#00E676"  # Green
    RARITY_RARE = "#2196F3"      # Blue
    RARITY_EPIC = "#9C27B0"      # Purple
    RARITY_LEGENDARY = "#FFD740" # Gold

    # Styles
    @classmethod
    def get_rich_theme(cls) -> RichTheme:
        """Get Rich theme configuration."""
        return RichTheme({
            "info": Style(color=cls.INFO),
            "success": Style(color=cls.SUCCESS, bold=True),
            "error": Style(color=cls.ERROR, bold=True),
            "warning": Style(color=cls.WARNING),
            "primary": Style(color=cls.PRIMARY, bold=True),
            "secondary": Style(color=cls.SECONDARY),
            "dim": Style(color=cls.TEXT_DIM, dim=True),
            "heading": Style(color=cls.PRIMARY, bold=True),
            "subheading": Style(color=cls.SECONDARY),
            "command": Style(color=cls.PRIMARY, bold=True),
            "points": Style(color=cls.WARNING, bold=True),
            "xp": Style(color=cls.SUCCESS, bold=True),
        })

    # Panel border styles
    PANEL_BORDER = "rounded"
    PANEL_BORDER_STYLE = Style(color=PRIMARY)

    # Progress bar colors
    PROGRESS_COMPLETE = Style(color=SUCCESS, bold=True)
    PROGRESS_INCOMPLETE = Style(color="grey30")

    @classmethod
    def get_rarity_style(cls, rarity: str) -> Style:
        """Get style for achievement rarity."""
        rarity_map = {
            "common": Style(color=cls.RARITY_COMMON),
            "uncommon": Style(color=cls.RARITY_UNCOMMON, bold=True),
            "rare": Style(color=cls.RARITY_RARE, bold=True),
            "epic": Style(color=cls.RARITY_EPIC, bold=True),
            "legendary": Style(color=cls.RARITY_LEGENDARY, bold=True, italic=True)
        }
        return rarity_map.get(rarity.lower(), Style(color="white"))

    @classmethod
    def get_difficulty_style(cls, difficulty: str) -> Style:
        """Get style for question difficulty."""
        if difficulty == "essential":
            return Style(color=cls.SUCCESS)
        else:
            return Style(color=cls.WARNING, bold=True)

    @classmethod
    def get_streak_color(cls, streak: int) -> str:
        """Get color for streak based on length."""
        if streak >= 20:
            return cls.ERROR  # Red hot!
        elif streak >= 10:
            return cls.WARNING  # Orange
        elif streak >= 5:
            return cls.PRIMARY  # Blue
        else:
            return cls.TEXT_SECONDARY  # Grey
