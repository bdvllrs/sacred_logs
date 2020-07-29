import click
import os

from .file_log import FileLog


@click.group()
def cli():
    """
    Entry point of the CLI. You can execute other commands from here.
    For example:
    Type a command with `--help` to get more information.
    """
    pass


@cli.command("tomongo", help="Export the file log to a mongo database.")
@click.argument("path")
@click.argument("db_name")
@click.option("--basedir", '-b', default=None, help="Base directory for the sources.")
@click.option("--url", "-u", default="127.0.0.1:27017", help="Url of the mongo database.")
@click.option("--overwrite", "-o", default=None, help="Id of an experiment to overwrite.")
@click.option("--skip_sources", "-s", is_flag=True, help="Do not include sources in the export.")
def tomongo(path, db_name, basedir, url, overwrite, skip_sources):
    """
    Export a file log to a mongo database
    """
    if basedir is None:
        basedir = os.getcwd()
    # Load a log
    log = FileLog(path)
    # Save if to a mongo database
    log.to_mongo(base_dir=basedir,
                 overwrite=overwrite,
                 remove_sources=skip_sources,
                 url=url,
                 db_name=db_name)
    click.echo("Exported.")


if __name__ == "__main__":
    cli()