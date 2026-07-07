import logging

logging.basicConfig(
    filename='octopus-paul-stats.log',
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8',
)

from application.cli import main

if __name__ == '__main__':
    main()
