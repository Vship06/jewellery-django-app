# constants.py

PRODUCT_CATEGORIES = [
    "BANGLE",
    "BRACELET",
    "CHAIN",
    "EARRINGS",
    "FINGER RING",
    "NECKLACE",
    "NOSE PIN",
    "PENDANT",
]

# CHANGE THESE TO ALL CAPS TO MATCH THE DB
AVAILABLE_METALS = ["GOLD", "PLATINUM"]

AVAILABLE_COLORS = [
    "YELLOW",
    "WHITE",
    "ROSE GOLD",
    "PINK",
    "MIX",
    "ROSE-WHITE",
    "YELLOW-WHITE",
]

# Keep these as they are (since your DB already has them matching)
AVAILABLE_PURITIES = ["14K", "18K", "22K", "950"]

AVAILABLE_CLARITIES = [
    "VVS",
    "VS",
    "VVS-VS",
    "SI",
    "POLKI",
    "PLAIN",
    "CUT AND POLISHED DIAMOND",
]

AVAILABLE_COLORS_D = ["DEF", "GH"]

DEFAULT_PRICE_MIN = 0
DEFAULT_PRICE_MAX = 4300000
