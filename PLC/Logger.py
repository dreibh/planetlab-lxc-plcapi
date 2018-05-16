import logging
import logging.config

# we essentially need one all-purpose logger
# that goes into /var/log/plcapi.log

plcapi_logging_config = {
    'version' : 1,
# we may be imported by something else, like sfa, so do not do that:
#    'disable_existing_loggers' : True,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
            'datefmt': '%m-%d %H:%M:%S'
        },
        'shorter': { 
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%d %H:%M:%S'
        },
    },
    'handlers': {
        'plcapi': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename' : '/var/log/plcapi.log',
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
