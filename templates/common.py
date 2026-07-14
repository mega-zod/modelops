from app.models.deployment import PlannedCommand


def sanitize_name(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value.lower()).strip("-")


def command(value: str, description: str) -> PlannedCommand:
    return PlannedCommand(command=value, description=description)
