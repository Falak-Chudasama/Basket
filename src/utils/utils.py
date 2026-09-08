from datetime import datetime

def get_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]