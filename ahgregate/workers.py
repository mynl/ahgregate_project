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
    (Path(dir_name) / 'img').mkdir(parents=True, exist_ok=True)
    logger.info(f'deleting all images in {dir_name}/img')
    for fn in (Path(dir_name) / 'img').glob('*.*'):
        fn.unlink()


def process_savefig(x, to_dir, hopper):
    """
    handle savfig -> fig_name.savefig()

    :param x: line containing @savefig
    :param to_dir: where to save
    :param hopper: list of lines to add to the end of the file
    :return:
    """

    fig_fn = x[2].split(' ')[0]
    # fig var name
    fig_var = f'fig_generated_{len(hopper)} = plt.gcf()\n'
    ffn = f'fig_generated_{len(hopper)}.savefig("{to_dir}/img/{fig_fn}")\n'.replace('\\', '/')
    hopper.append(ffn)
    return fig_var


def rst_to_py_work(fn, to_dir):
    """
    Actually does the work for a single file

    :param fn:
    :param to_dir:
    :return:
    """

    logger.info(f'from {fn} to {to_dir}')

    txt = fn.read_text(encoding='utf-8')

    # find the ipython code blocks and extract
    # some files have three space indents
    # strictly four space tabs: split on ipython: , pull out right parts; remove leading tabs, remove @savefig
    # split at the start of .. ipython directives
    stxt = re.split(r'.. ipython:: +python\n( +:okwarning:\n)?( +:suppress:\n)?( +:okexcept:\n)?', txt)[4::4]

    # need to find the end of the python part, look for one or more newlines followed by a character at
    # the start of the line; $ for potential equations, . for other directives, ` for rst e.g. ``var``
    # : for a directive, # for a list
    # * for bold; --- or === for a horizontal line; when indendented the line may start with two spaces
    code0 = [re.split('\n\n+ ? ?[A-Za-z0-9$.*`:#=\-]', s)[0] for s in stxt]

    # find savefigs, replace with plt.savefig and store...these must all be processed at the end
    # code1 = [re.sub('^[ \t]*@savefig[^\n]+\n', '', s, flags=re.MULTILINE) for s in code0]
    hopper = []
    f = lambda x: process_savefig(x, to_dir, hopper)
    code1 = [re.sub('^([ \t]*)@savefig ([^\n]+)\n', f, s, flags=re.MULTILINE) for s in code0]

    # move one tab to the left
    python_code = [re.sub('\n    ?', '\n', i)  for i in code1]

    # prepend hopper code before close all'
    newcode = '\n'.join(hopper)
    for i, l in enumerate(python_code):
        if l.find("plt.close('all')") >= 0:
            python_code[i] = python_code[i].replace("plt.close('all')", f"{newcode}\nplt.close('all')")
            newcode = ''
    if newcode != '':
        # add at end
        python_code.append(newcode)

    # close up unnecessary newlines
    python_code = [re.sub(r'\n\n+', r'\n\n', i) for i in python_code]

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

    return str_out

def r(l):
    """ for debugging """
    for i, b in enumerate(l):
        print(i)
        print(b)
        print('='*50)



def rst_to_py_dir_work(from_dir, to_dir):
    if from_dir == 'doc':
        from_dir = 'c:\\s\\telos\\python\\aggregate_project\\doc'

    from_dir = Path(from_dir)
    logger.info(from_dir.resolve())
    assert from_dir.exists()

    delete_files(to_dir)

    for i, fn in enumerate(Path(from_dir).glob('**/*.rst')):
        logger.info(f'Converting file {i}:  {fn}')
        rst_to_py_work(fn, to_dir)


