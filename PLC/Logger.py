# pylint: disable=c0103

import logging
import logging.config

# we essentially need one all-purpose logger
# that goes into /var/log/plcapi.log

plcapi_logging_config = {
    'version': 1,
    # IMPORTANT: we may be imported by something else, like sfa, so:
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'datefmt': '%m-%d %H:%M:%S',
            'format': ('%(asctime)s %(levelname)s '
                       '%(filename)s:%(lineno)d %(message)s'),
        },
    },
    'handlers': {
        'plcapi': {
            'filename': '/var/log/plcapi.log',
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'plcapi': {
            'handlers': ['plcapi'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

logging.config.dictConfig(plcapi_logging_config)

# general case:
# from PLC.Logger import logger
logger = logging.getLogger('plcapi')

#################### test
if __name__ == '__main__':
    logger.info("in plcapi")
