Creating a Custom Logger
========================

3DB can generate huge amounts of data. In most cases, it would be impractical
to store all of it. Moreover, it would be hard to come up with a data format
that suits all users. To solve that challenge, we introduce the concept of loggers.

Loggers are simply classes that receive all the information available to the
framework and decide what to store and it which format. Even if we ship the
library with a set of Loggers (TODO LINK to API), we want it to be easy for
users to define their own.

To illustrate how to create a custom logger we will go through the whole process
and implement ``CSVLogger``, a logger that outputs basic informations about a render
to a CSV file.

Implementation
--------------

First we have to subclass the provided base class: :class:`threedb.result_logging.base_logger.BaseLogger`:

.. code-block:: python

    from threedb.result_logging.base_logger import BaseLogger

    class CSVLogger(BaseLogger):
        pass

In order to make this a valid logger, we need to provide implementations of two
abstract functions: ``__init__``, and ``log()``. 

.. code-block:: python

    def __init__(self, root_dir: str, result_buffer: BigChungusCyclicBuffer, config: Dict[str, Dict[str, Any]]) -> None:
        super().__init__(root_dir, result_buffer, config)
        fname = path.join(root_dir, 'details.csv')  # Where we will store the data
        self.handle = open(fname, 'w')  # Opening the file
        self.regid = self.buffer.register()  # Obtain a unique logger id (see Note below)
        self.first = True

Next, we need to implement the ``log()`` function, which is called whenever a
new result is available to log.

.. code-block:: python

    def log(self, item):
        if item is None:
            self.handle.close()  # We close the file handle when there is nothing left to log

        # The item argument will contain all information about the job that we are logging
        # and the key 'result_ix', which tells us where in the buffer the data for the
        # results is located.
        # To access the results themselves we simply have to index the buffer with this index.
        rix = item['result_ix']  # Getting the index
        buffer_data = self.buffer[rix]  # Getting the result information

        if self.first:  # We write the headers of the file if this is the first row
            param_keys = list(item['render_args'].keys())
            self.handle.write(['Id', 'correct'] + param_keys)
            self.handle.write('\n')
            self.first = False

        self.handle.write(','.join([item['id'], buffer_data['is_correct']] + list(item['render_args'].values())))
        self.handle.write('\n')
        self.buffer.free(rix, self.regid)  # IMPORTANT: We tell the buffer we are done with the data

Since Loggers are dynamically loaded based on the configuration file, the frameworks need to know
which object to load from the module. By convention we ask that logger modules export the ``Logger``
field. So we simply have to add:

.. code-block:: python

    Logger = CSVLogger

Our custom logger is now fully functional.

.. note::

    To ensure that they do not perturb and/or slow down the scheduler, each logger
    runs in a separate python process. But, because the amount of data generated
    is substantial, we found that transmitting the data from the scheduler to the
    Logger classes was a major bottleneck. As a result, we decided to use
    shared memory instead. The scheduler places the information in a buffer and passes
    a reference instead. Because we eventually need to release the memory used for a result,
    we maintain a reference counter for each entry in the buffer in shared memory.

    To be able to keep track of Loggers, they have to request a unique identifier from the
    ``BigChungusCyclicBuffer``. Moreover, they have to notify the buffer when they are
    done reading the information from the buffer using ``free()``. This way the scheduler
    will reuse the memory for an upcoming render. Failure to do so will result in the
    system hanging when the buffer is full of unreleased entries.

Utilization
-----------

Once your custom logger is defined, the only thing you have left to do is to add it
to your configuration file in the ``logging`` section:

.. code-block:: yaml

  logging:
    logger_modules:
      - "path.to.my.module"

We assume here that ``path.to.my.module`` points to the file we created in the section above.
You can make this module available in any way you see fit:

* Make a pip package
* Add the proper folder to ``$PYTHON_PATH``
* Create and install a local package
* ...
