

class Input_Name:
	@staticmethod
	def input_name():
		your_name = str(input(
			"""Welcome to PyRPG.
		This project is a text based input-output RPG game.
		Please read #patch_notes file to see new patches or features.
		To start you off, please input your name: """))
		globals()["your_name"] = your_name
		return your_name
	