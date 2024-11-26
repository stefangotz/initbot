from initbot.state.local import LocalState
from initbot.state.sql import SqlState


if __name__ == "__main__":
    json_state = LocalState()
    sql_state = SqlState()
    sql_state.import_from(json_state)
