# src/core/cmb/cmb_router_entry.py

import argparse
from src.core.cmb.cmb_router import ChannelRouter  # or whatever your class is named

def main():
    parser = argparse.ArgumentParser(description="CMB Channel Router")
    parser.add_argument("--channel", required=True, help="Channel name (e.g. CC, VB)")
    args = parser.parse_args()

    router = ChannelRouter(channel_name=args.channel)
    router.start()   # or start(), loop(), etc.
    

if __name__ == "__main__":
    main()
