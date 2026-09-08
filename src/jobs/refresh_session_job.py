from src.core.state import quince_memory, quince_commands

def clear_session():
    quince_memory.clear_short_term()
    quince_commands.delete_all_temp()