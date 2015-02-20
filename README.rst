Mongo-Logger
============

This module creates a logger ``mongologger`` which once enabled logs all queries to MongoDB.

.. code-block:: python

    import mongologger
    mongo_log = mongologger.create_logger(stack_size=0)  # show no call stack
    LOGGING['loggers'][mongo_log.name] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False,
    }
