import pdfkit
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

templates_dir = Path(__file__).parent.parent / "templates"
env = Environment(loader=FileSystemLoader(templates_dir))


def render_pdf(template_name: str, context: dict) -> bytes:
    template = env.get_template(template_name)
    html = template.render(context)
    pdf = pdfkit.from_string(html, False)  # False → вернуть как bytes
    return pdf
