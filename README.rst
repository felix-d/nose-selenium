nose-selenium
*************

A Selenium WebDriver plugin for nose.

Thank you to `Dave Hunt <http://github.com/davehut>`_ for doing
this work first for py.test in
`pytest-mozwebqa <http://github.com/davehunt/pytest-mozwebqa>`_.

Currently, this plugin deals only with input parameters, and does not
modify the results reporting in any way.

nosetests command line options
==============================

.. code-block:: bash

    $ nosetests --with-nose-selenium --help
    Usage: nosetests [options]

    Options:
      -h, --help            show this help message and exit
      -V, --version         Output nose version and exit
      -p, --plugins         Output list of available plugins and exit. Combine
                            with higher verbosity for greater detail
      -v, --verbose         Be more verbose. [NOSE_VERBOSE]
    [snip]
      --with-nose-selenium  Enable plugin NoseSelenium: None
                            [NOSE_WITH_NOSE_SELENIUM]
      --config-file         Load options from ConfigParser compliant config file.
                            Values in config file will override values sent on the
                            command line.
      --browser=BROWSER     Run this type of browser (default ['FIREFOX'], options
                            for local [FIREFOX, INTERNETEXPLORER, CHROME], options
                            for remote/grid/sauce [ANDROID, CHROME, FIREFOX,
                            HTMLUNIT, HTMLUNITWITHJS, INTERNETEXPLORER, IPAD,
                            IPHONE, OPERA, PHANTOMJS, SAFARI]). May be stored in
                            environmental variable SELENIUM_BROWSER.
      --build=str           build identifier (for continuous integration). Only
                            used for sauce.
      --browser-version=BROWSER_VERSION
                            Run this version of the browser. (default:  implies
                            latest.)
      --os=OS               Run the browser on this operating system. (default:
                            none, options [windows, mac, linux], required for grid
                            or sauce)
      --timeout=num         timeout (in seconds) for page loads, etc. (default:
                            60)

Example Commands
----------------

.. code-block:: bash

    $ nosetests --with-nose-selenium --browser=FIREFOX
    $ nosetests --with-nose-selenium --config-file=selenium.conf


Writing test scripts with nose-selenium
=======================================
Loading configuration from a config file
---------------------------------
If you use the --config-file flag, the rest of the command-line flags
will be ignored. The same defaults values for optional keys apply, and
validation checking will be performed when involked from nosetests.

**Example selenium.conf file**

Not all keys are required for all configurations, read the command-line
options section above for clues. Where values are provided, they are the
defaults.

.. code-block:: bash

    [SELENIUM]
    BROWSER: FIREFOX
    BUILD:
    BROWSER_VERSION:
    OS:
    TIMEOUT: 60


Inheriting from SeleniumTestCase
--------------------------------

SeleniumTestCase creates the webdriver and stores it in self.wd in its setUp()
and closes it in tearDown().

.. code-block:: python

    from nose_selenium import SeleniumTestCase


    class MyTestCase(SeleniumTestCase):

        def test_that_google_opens(self):
            self.wd.get("http://google.com")
            self.assertEqual(self.wd.title, "Google")

Using ScreenshotOnExceptionWebDriver
------------------------------------
ScreenshotOnExceptionWebDriver is designed to take a screenshot, fetch the
html, and log the url before reporting any WebDriverException. It excludes
exceptions encountered by WebDriverWait's until() and until_not() methods.

Using ScreenshotOnExceptionWebDriverWait
----------------------------------------
If you want screenshots and html to be captured for TimeoutException-s
raised by WebDriverWait, use ScreenshotOnExceptionWebDriverWait in its
place.

Using setup_selenium_from_config()
----------------------------------
If you'd like to use ``ScreenshotOnExceptionWebDriver`` or
``ScreenshotOnExceptionWebDriverWait`` without using the nose framework,
you can put its settings in a ConfigParser compliant file with a [SELENIUM]
section and call ``setup_selenium_from_config`` with a ConfigParser instance which
has read from this file. This will set up the variables so that
``build_webdriver`` can read them.

.. code-block:: python

    from nose_selenium import build_webdriver, setup_selenium_from_config
    from ConfigParser import ConfigParser

    CONFIG = ConfigParser()
    CONFIG.read('selenium.conf')

    setup_selenium_from_config(CONFIG)
    wd = build_webdriver()


.. note::

    If you use portions of this library without using nose, validity checking
    will not be performed.
