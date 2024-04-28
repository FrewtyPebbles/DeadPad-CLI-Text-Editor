
FG_COLORS = {
    "gray":30,
    "red":31,
    "green":32,
    "yellow":33,
    "blue":34,
    "purple":35,
    "cyan":36,
    "white":37
}

STYLES = {
    "default":0,
    "bold":1,
    "faded":2,
    "italic":3,
    "underline":4,
    "crossthrough":9
}

BG_COLORS = {
    "default":38,
    "black":40,
    "red":41,
    "green":42,
    "yellow":43,
    "blue":44,
    "purple":45,
    "cyan":46,
    "white":47,
}

RESET_STYLE = "\x1b[0m"

def get_style(fg:str = "white", bg:str = "default", style:str = "default"):
    """
    Returns the ascii escape code for the color requested
    """
    return f"\x1b[{STYLES[style]};{FG_COLORS[fg]};{BG_COLORS[bg]}m"