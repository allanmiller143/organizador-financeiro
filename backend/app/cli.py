import click
from flask import Flask

from app.services import cdi_service


def register_cli(app: Flask) -> None:
    @app.cli.command("sync-cdi")
    @click.option(
        "--from",
        "start",
        type=click.DateTime(formats=["%Y-%m-%d"]),
        default=None,
        help="Data inicial no formato AAAA-MM-DD.",
    )
    def sync_cdi_command(start):
        """Baixa do Banco Central os dias de CDI que faltam."""
        inserted = cdi_service.sync_cdi(start=start.date() if start else None)
        click.echo(f"{inserted} novos dias de CDI gravados.")