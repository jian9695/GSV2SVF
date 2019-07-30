import argparse
import ast
import logging
import os

from python2.server.server import Python2Server


logger = logging.getLogger(__name__)


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Python 2 server")
    parser.add_argument('--in', '-i', dest='in_', type=int, default=0,
                        help="File descriptor for server input")
    parser.add_argument('--out', '-o', type=int, default=1,
                        help="File descriptor for server output")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--logging-basic',
                       help="Keyword arguments for logging.basicConfig()")
    group.add_argument('--logging-dict',
                       help="Dict to pass to logging.config.dictConfig()")
    return parser.parse_args(args=args)


def configure_logging(conf):
    if conf.logging_basic is not None:
        logging.basicConfig(**ast.literal_eval(conf.logging_basic))
    if conf.logging_dict is not None:
        logging.config.dictConfig(ast.literal_eval(conf.logging_dict))
    else:
        logging.basicConfig()


def run_server(conf):
    server = Python2Server(os.fdopen(conf.in_, 'rb'),
                           os.fdopen(conf.out, 'wb'))
    logger.info('Python 2 server started')
    try:
        server.run()
    except Exception:
        logger.error('Python 2 server aborting', exc_info=True)
        raise
    else:
        logger.info('Python 2 server exited cleanly')


def main(args=None):
    conf = parse_args(args)
    configure_logging(conf)
    run_server(conf)


if __name__ == '__main__':
    main()
