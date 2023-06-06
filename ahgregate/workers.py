# Functions called from scripts
import logging
from pathlib import Path
import re

from .test import test_scripts_work

logger = logging.getLogger(__name__)

def delete_files(dir_name, pattern='*.*'):
    """
    Delete files matching pattern in dir_name.

    :param dir_name:
    :param pattern:
    :return:
    """
    for fn in Path(dir_name).glob(pattern):
        logger.info(f'deleting {fn}')
        fn.unlink()


def rst_to_py_work(fn, to_dir):
    """
    Actually does the work.

    :param fn:
    :param to_dir:
    :return:
    """

    logger.info(f'from {fn} to {to_dir}')

    # (Path(to_dir) / "img").mkdir(parents=True, exist_ok=True)
    #
    # def f(x):
    #     # handle savfig -> plt.gcf().savefig()
    #     fig_fn = x[2].split(' ')[0]
    #     ffn = f'{x[1]}plt.gcf().savefig("{to_dir}/img/{fig_fn}")\n'.replace('\\', '/')
    #     return ffn

    txt = fn.read_text(encoding='utf-8')
    # can do this in one line, but it is incomprehensible
    # strictly four space tabs: split on ipython: , pull out right parts; remove leading tabs, remove @savefig
    stxt = re.split(r'.. ipython:: +python\n( +:okwarning:\n)?( +:suppress:\n)?', txt)[3::3]
    code0 = [re.split('\n\n+', s)[0] for s in stxt]
    code1 = [re.sub('^[ \t]*@savefig[^\n]+\n', '', s, flags=re.MULTILINE) for s in code0]
    # code1 = [re.sub('^([ \t]*)@savefig ([^\n]+)\n', f, s, flags=re.MULTILINE) for s in code0]
    python_code = [re.sub('\n    ?', '\n', i)  for i in code1]

    # reassemble
    str_out = '\n'.join(python_code)
    if len(str_out) > 0:
        logger.info(str_out)
        fout = (Path(to_dir) / fn.name).with_suffix('.py')
        fout.parent.mkdir(parents=True, exist_ok=True)
        logger.info(fout)
        fout.write_text(str_out, encoding='utf-8')
    else:
        logger.info('No Python code found in file.')


def rst_to_py_dir(from_dir, to_dir):
    if from_dir == 'doc':
        from_dir = 'c:\\s\\telos\\python\\aggregate_project\\doc'

    from_dir = Path(from_dir)
    logger.info(from_dir.resolve())
    assert from_dir.exists()

    delete_files(to_dir)

    for i, fn in enumerate(Path(from_dir).glob('**/*.rst')):
        logger.info(f'Converting file {i}:  {fn}')
        rst_to_py_work(fn, to_dir)
