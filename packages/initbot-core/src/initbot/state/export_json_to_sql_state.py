# Tool for converting JSON state to SQL state
# Invoke as follows:
# uv run -m initbot.state.export_json_to_sql_state DIR_WITH_JSON_FILES SQLITE_FILE
import sys

from .local import LocalState
from .sql import SqlState

if __name__ == "__main__":
    json_state = LocalState(sys.argv[1])
    sql_state = SqlState(f"sqlite:{sys.argv[2]}")
    sql_state.import_from(json_state)
