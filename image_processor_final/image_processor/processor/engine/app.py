from flask import Flask


def create_app():
    """create app named image_processor and reurn the app."""
    return Flask("image_processor", template_folder="processor/templates", static_folder="processor/static")
