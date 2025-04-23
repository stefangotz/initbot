import sys

from .local import LocalState
from .sql import SqlState

if __name__ == "__main__":
    json_state = LocalState(sys.argv[1])
    sql_state = SqlState.create_with_sqlite(sys.argv[2])
    sql_state.import_from(json_state)
