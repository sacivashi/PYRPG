from game_data.data_inputs.input_name.input_name import Input_Name
from game_data.data_inputs.save_input.save_state import Save_State


class PYRPG:
	@staticmethod
	def start():
		name = Input_Name.input_name()
		Save_State.save_state(name)


PYRPG.start()
