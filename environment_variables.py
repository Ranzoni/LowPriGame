import os

def load_config(variables: dict[str, str]) -> dict[str, str]:
    """Carrega e valida as variáveis de ambiente necessárias."""

    config = {}
    for key, value in variables.items():
        config[key] = os.getenv(value)

    missing = [key for key, value in config.items() if not value]
    if missing:
        formatted = ", ".join(missing)
        raise ValueError(f"Variáveis de ambiente ausentes: {formatted}")
    
    return config