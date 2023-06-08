
import asyncio
from bs4 import BeautifulSoup
import logging
from pathlib import Path
import shutil
import shlex

logger = logging.getLogger(__name__)


async def run_sphinx(cmd):
    """
    Run a command in a subprocess and look for errors.

    :param worker: name of worker, just for interest.
    :param cmd: command to run (usually ipython filename)
    :return:
    """

    logger.info(f'running {cmd}')
    args = shlex.split(cmd, posix=False)

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info(f'[OK:    {cmd!r} exited with {proc.returncode}]')
    else:
        # this is the trigger there was an error, not finding the word Error
        # in the output. That can be legitimate output. Hence:
        logger.warning(f'[ERROR: {cmd!r} exited with {proc.returncode}]')
    fn = args[1]
    if stdout:
        so = stdout.decode()
        first_error = so.find('Error')
        if first_error >= 0 and proc.returncode:
            logger.error(so[first_error-100:])

    return proc.returncode


def ipytho_to_rst(fn_in, dir_out='\\temp\\z\\BLANK_OUT', rebuild=True):
    """
    fn_in is rst file containing ipython directives, that are potentially
    time-consuming to run. It should not be in BLANK, it is copied into index.rst there.

    dir_out is where an rst file converted to html and included in a raw directive
    blob.

    Workflow

    * save fn_in as index.rst in \\temp\\z\\BLANK
    * build BLANK using sphinx-build - it should be fast, it has only one file.
    * Extract html blob of page details form \\_build\\html\\index.rst
    * create new page with same name as fn_in blog in dir_out (typically in another project?)
    * copy resources: graphs from savefig into _build\\html\\_images

    """

    blank_dir = Path('\\temp\\z\\BLANK')
    assert blank_dir.exists(), 'BLANK must exist'

    fn_in = Path(fn_in)
    assert fn_in.exists()

    logger.info(f'reading {fn_in}')
    txt_in = fn_in.read_text(encoding='utf-8')

    logger.info(f'writing {blank_dir / "index.rst"}')
    (blank_dir / 'index.rst').write_text(txt_in, encoding = 'utf-8')

    # run sphinx-build
    if rebuild:
        logger.info('running sphinx-build')
        returncode = asyncio.run(run_sphinx('sphinx-build -b html '
                                        '-d \\temp\\z\\BLANK\\_build\\doctrees '
                                        '\\temp\\z\\BLANK '
                                        '\\temp\\z\\BLANK\\_build\\html '
                                        ))
        logger.info(f'sphinx-build returned {returncode}')

    # extract html blob
    logger.info('extracting html blob')
    html_blob = (blank_dir / '_build\\html\\index.html').read_text(encoding='utf-8')
    soup = BeautifulSoup(html_blob, 'html.parser')
    blobs = soup.find_all('div', class_='body', role='main')
    assert len(blobs) == 1, 'Should be one blob'

    # tabify blob
    logger.info('tabifying blob')
    blob = blobs[0].prettify()
    blob = '\n'.join([f'\t{line}' for line in blob.splitlines()])

    # create new page with blob in fn_out
    new_rst = f"""
Here is Generated Page
=======================

Start embedded html

.. raw:: html

{blob}

End embedded html
    
"""

    fn_out = Path(f'{dir_out}\\{fn_in.stem}.rst')
    logger.info(f'saving new rst with embedded html blob at {fn_out}')
    fn_out.write_text(new_rst, encoding='utf-8')

    # link graphs
    logger.info('linking graphs')
    savefig_in = (blank_dir / 'savefig')
    savefig_dir = (fn_out.parent / '_build\\html\\_images')
    savefig_dir.mkdir(exist_ok=True, parents=True)

    # ??! will these exist if orginals deleted?
    for fn in savefig_in.glob('*'):
        logger.info(f'linking {fn}')
        (savefig_dir / fn.name).hardlink_to(fn)

    logger.info('remember to rerun sphinx in BLANK2 to get new page')