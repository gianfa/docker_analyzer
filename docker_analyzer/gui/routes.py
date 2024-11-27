import docker
import pandas as pd
from bs4 import BeautifulSoup
from flask import Blueprint, redirect, render_template, request, url_for

from docker_analyzer.analysis import make_analysis_1
from docker_analyzer.logger import logging

logger = logging.getLogger(__name__)

ui_blueprint = Blueprint("ui", __name__)


def get_docker_images():
    try:
        client = docker.from_env()
        images = client.images.list()
        image_tags = [img.tags[0] if img.tags else str(img.id) for img in images]
        return image_tags
    except docker.errors.DockerException as e:
        logger.error(f"Error retrieving Docker images: {e}")
        return []


def add_css_to_createdby_column(html_table: str, original_df: pd.DataFrame) -> str:
    """
    Adds a custom CSS class to the 'CreatedBy' column only in the header (thead).

    Parameters
    ----------
    html_table : str
        L'HTML generato dal DataFrame.
    original_df : pd.DataFrame
        Il DataFrame originale.

    Returns
    -------
    str
        The modified HTML with the CSS class added to the 'CreatedBy' column in the header.
    """
    # Analyze the HTML
    soup = BeautifulSoup(html_table, "html.parser")

    if "CreatedBy" not in original_df.columns:
        return html_table

    # Find the 'CreatedBy' column index in the table header
    thead = soup.find("thead")
    headers = thead.find_all("th") if thead else []
    createdby_index = None

    for i, header in enumerate(headers):
        header["data-title"] = header.get_text(strip=True)  # Add the tooltip
        if "CreatedBy" in header.get_text(strip=True):
            header["class"] = header.get("class", []) + [
                "created-by-column",
                "text-wrap",
            ]
            createdby_index = i

    return str(soup)


@ui_blueprint.route("/", methods=["GET", "POST"])
def index():
    """Render the main page with image selection."""

    if request.method == "POST":
        img1 = request.form.get("img1")
        img2 = request.form.get("img2")
        return redirect(url_for("ui.compare_images", img1=img1, img2=img2))

    images = get_docker_images()

    return render_template("index.html", images=images)


@ui_blueprint.route("/compare", methods=["POST"])
def compare_images():
    """Esegue l'analisi e mostra le views."""

    image_name1 = request.form.get("img1")
    image_name2 = request.form.get("img2")

    views = make_analysis_1(image_name1, image_name2)

    # Convert DataFrame to HTML and add the CSS class to the 'CreatedBy' column
    for view in views:
        if view["df"].empty:
            view["df"] = ""
        else:
            view_html = view["df"].to_html(classes="table table-striped")
            view["df"] = add_css_to_createdby_column(view_html, view["df"])

    return render_template(
        "results.html", views=views, img1=image_name1, img2=image_name2
    )
