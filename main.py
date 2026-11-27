# #  """
# Main entry point for PYRPG
# Run with: python main.py
# """

if __name__ == "__main__":
    from util.display import enable
    enable()  # colors (Rich), when it's installed and this is a real terminal
    from game.pyrpg import PYRPG
    PYRPG()
