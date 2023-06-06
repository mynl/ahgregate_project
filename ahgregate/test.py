"""
This module will run a set of scripts in subprocesses and look for errors.
It is used in conjunction with rst_to_py to test the code in the documentation.

Code based on example from https://docs.python.org/3.10/library/asyncio-queue.html
"""
import asyncio
import logging
import shutil
import shlex
import time
from pathlib import Path

logger = logging.getLogger(__name__)


async def run_cmd(worker, cmd):
    """
    Run a command in a subprocess and look for errors.

    :param worker: name of worker, just for interest.
    :param cmd: command to run (usually ipython filename)
    :return:
    """

    # todo...not generic
    args = shlex.split(cmd, posix=False)
    # logger.info(args)
    logger.info(shutil.which(args[0]))

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.info(f'[OK:    {cmd!r} exited with {proc.returncode} // {worker}]')
    else:
        logger.warning(f'[ERROR: {cmd!r} exited with {proc.returncode} // {worker}]')
    fn = args[1]
    if stdout:
        so = stdout.decode()
        first_error = so.find('Error')
        p = Path(fn)
        if first_error >= 0:
            logger.warning(f'        errors for {cmd!r}')
            p.with_suffix('.error').write_text(so[first_error:], encoding='utf-8')
        # also write the whole thing
        p.with_suffix('.output').write_text(so, encoding='utf-8')
    if stderr:
        se = stderr.decode()
        if len(se) > 0:
            p = Path(fn)
            p.with_suffix('.stderr').write_text(se, encoding='utf-8')


async def worker(name, queue):
    while True:
        # Get a "work item" out of the queue.
        fn_path = await queue.get()

        await run_cmd(name, f'ipython {fn_path}')

        # Notify the queue that the "work item" has been processed.
        queue.task_done()


async def test_scripts_work(dir_name, pattern='*.py', n_workers=7):
    """
    Run all the scripts in a directory in parallel.

    :param dir_name:
    :param pattern:
    :param n_workers:
    :return:
    """
    # Create a queue that we will use to store our "workload".
    queue = asyncio.Queue()

    # Generate random timings and put them into the queue.
    for fn in Path(dir_name).glob(pattern):
        queue.put_nowait(fn.resolve())

    # Create three worker tasks to process the queue concurrently.
    tasks = []
    for i in range(n_workers):
        task = asyncio.create_task(worker(f'worker-{i}', queue))
        tasks.append(task)

    # Wait until the queue is fully processed.
    started_at = time.monotonic()
    await queue.join()
    total_wall_time = time.monotonic() - started_at

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()

    # Wait until all worker tasks
    # are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.warning('====')
    logger.warning(f'7 workers in parallel for {total_wall_time:.2f} seconds wall time')
