import asyncio
import click
import logging

from .workers import *

# __all__ = ['main', "py_rst_to_md", "py_all_rst_to_md"]

logger = logging.getLogger(__name__)


class Repo:
    def __init__(self, home):
        self.home = home
        self.config = {}
        self.verbose = False

    def set_config(self, key, value):
        self.config[key] = value
        if self.verbose:
            click.echo(f"  config[{key}] = {value}", file=sys.stderr)

    def __repr__(self):
        return f"<Repo {self.home}>"


pass_repo = click.make_pass_decorator(Repo)


@click.group()
@click.option(
    "--repo-home",
    envvar="REPO_HOME",
    default=".repo",
    metavar="PATH",
    help="Changes the repository folder location.",
)
@click.option(
    "--config",
    nargs=2,
    multiple=True,
    metavar="KEY VALUE",
    help="Overrides a config key/value pair.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("1.0")
@click.pass_context
def main(ctx, repo_home, config, verbose):
    """Repo is a command line tool that showcases how to build complex
    command line interfaces with Click.

    This tool is supposed to look like a distributed version control
    system to show how something like this can be structured.
    """
    # Create a repo object and remember it as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_repo decorator.
    ctx.obj = Repo(repo_home)
    ctx.params = dict()
    ctx.obj.verbose = verbose
    for key, value in config:
        ctx.params[key] = value
    if verbose:
        print(ctx.params)


@main.command()
@click.option("--username", prompt=True, help="The developer's shown username.")
@click.option("--email", prompt="E-Mail", help="The developer's email address")
@click.password_option(help="The login password.")
@pass_repo
def setuser(repo, username, email, password):
    """Sets the user credentials.

    This will override the current user config.
    """
    repo.set_config("username", username)
    repo.set_config("email", email)
    repo.set_config("password", "*" * len(password))
    click.echo("Changed credentials.")


@main.command(short_help="Convert ipython code in rst file into a py file.")
@click.argument("fns", nargs=-1, type=click.Path())
@click.argument("to-dir", type=click.Path())
def rst_files_to_py(fns, to_dir):
    """
    Strip ipython code out of rst file and make md file that can be read into
    Jupyter using Jupytext.
    """
    for fn in fns:
        fn = Path(fn)
        assert fn.exists()
        rst_to_py_work(fn, to_dir)


@main.command(short_help="Convert ipython code in all rst file in from-dir into a Jupytext md file.")
@click.argument("from-dir", type=click.Path())
@click.argument("to-dir", type=click.Path())
def rst_to_py(from_dir, to_dir):
    """
    Convert code in all rst files in from_dir to md files
    """
    rst_to_py_dir(from_dir, to_dir)
    if from_dir == 'doc':
        from_dir = 'c:\\s\\telos\\python\\aggregate_project\\doc'

    from_dir = Path(from_dir)

    logger.info(from_dir.resolve())
    assert from_dir.exists()

    for i, fn in enumerate(Path(from_dir).glob('**/*.rst')):
        logger.info(f'Converting file {i}:  {fn}')
        rst_to_py_work(fn, to_dir)


@main.command(short_help="Test all Python scripts in directory.")
@click.argument("dir-name", type=click.Path())
@click.argument("pattern", type=str, default='*.py')
@click.argument("n-workers", type=int, default=7)
def test_scripts(dir_name, pattern, n_workers):
    asyncio.run(test_scripts_work(dir_name, pattern=pattern, n_workers=n_workers))


@main.command(short_help="Quick test of documentation for aggregate. Optionally subset by pattern.")
@click.argument("dir-name", type=click.Path(), default='\\temp\\z\\agg_doctest')
@click.argument("pattern", type=str, default='*.py')
@click.argument("n-workers", type=int, default=7)
def agg_test(dir_name, pattern, n_workers):
    print(dir_name, pattern, n_workers)
    rst_to_py_dir('doc', dir_name)
    asyncio.run(test_scripts_work(dir_name, pattern=pattern, n_workers=n_workers))

