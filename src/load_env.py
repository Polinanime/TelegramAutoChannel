from dotenv import dotenv_values

def load_env():
    config = dotenv_values(".env")
    return config