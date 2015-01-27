Mongo-Logger
============

This module creates a logger ``mongologger`` which once enabled logs all queries to MongoDB.

.. code-block:: python

    LOGGING['loggers']['mongologger'] = {
        'level': 'INFO',
        'handlers': ['console'],
    }
    import mongologger
    mongologger.create_logger()
