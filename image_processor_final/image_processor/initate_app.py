from processor.engine.app import create_app


run_app = create_app()
with run_app.app_context():
    from processor.controllers import *


if __name__ == "__main__":
    run_app.run(
        host="0.0.0.0",
        port=2525,
        debug=True,
        threaded=True
    )
