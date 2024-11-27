from flask import Flask, render_template

from docker_analyzer import config


def create_app():
    """Create and configure the Flask app."""
    print("Creating Flask app...")
    app = Flask(__name__)

    # Adding configuration variables to the app context
    app.config["AUTHOR_NAME"] = config.AUTHOR_NAME
    app.config["AUTHOR_SURNAME"] = config.AUTHOR_SURNAME
    app.config["GITHUB_URL"] = config.GITHUB_URL
    app.config["PROJECT_TITLE"] = config.PROJECT_TITLE
    app.config["IMAGE_SELECTOR_TITLE"] = config.IMAGE_SELECTOR_TITLE
    app.config["IMAGE_SELECTOR_SUBTITLE"] = config.IMAGE_SELECTOR_SUBTITLE
    app.config["IMAGE_SELECTOR_DESC"] = config.IMAGE_SELECTOR_DESC

    @app.errorhandler(404)
    def page_not_found(e):
        """
        Render a custom 404 error page when an invalid URL is accessed.

        Parameters
        ----------
        e : Exception
            The exception raised for the 404 error.

        Returns
        -------
        Rendered HTML page.
        """
        return render_template("404.html"), 404

    with app.app_context():
        from .routes import ui_blueprint

        app.register_blueprint(ui_blueprint)
        return app


if __name__ == "__main__":
    app = create_app()
    print("Starting Flask app...")
    app.run(host="0.0.0.0", port=config.WEB_APP_PORT, debug=True)
