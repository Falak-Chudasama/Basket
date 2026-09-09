from src.core.state import quince_memory, quince_commands, states


def clear_session():
    quince_memory.clear_short_term()
    quince_commands.delete_all_temp()
    states["quince_active_session"] = False
    states["quince_active_session_id"] = None
