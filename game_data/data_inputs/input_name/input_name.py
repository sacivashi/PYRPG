

class Input_Name:
	@staticmethod
	def input_name():
		your_name = str(input(
			"""Welcome to PyRPG.
This project is a text based RPG game.
Please look at patch notes files to see new patches or features.
To start you off, please input your name: """))
		return your_name
	