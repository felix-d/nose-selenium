import os
import requests
import time
import inspect
import json
from unittest2 import TestCase

from nose.plugins import Plugin
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from configparser import ConfigParser

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

BROWSER = None
BUILD = None
BROWSER_VERSION = None
OS = None
TIMEOUT = None

def setup_selenium_from_config(config):
    """Start selenium with values from config file, or defaults
    rather than requiring the command-line options. File must be
    ConfigParser compliant and have a section called 'SELENIUM'.
    """
    global BROWSER
    global BUILD
    global BROWSER_VERSION
    global OS
    global TIMEOUT

    if config.has_option("SELENIUM", "BROWSER"):
        BROWSER = config.get("SELENIUM", "BROWSER")
    else:
        BROWSER = 'FIREFOX'

    if config.has_option("SELENIUM", "BUILD"):
        BUILD = config.get("SELENIUM", "BUILD")

    if config.has_option("SELENIUM", "BROWSER_VERSION"):
        BROWSER_VERSION = config.get("SELENIUM", "BROWSER_VERSION")

    if config.has_option("SELENIUM", "OS"):
        OS = config.get("SELENIUM", "OS")

    if config.has_option("SELENIUM", "TIMEOUT"):
        TIMEOUT = config.getfloat("SELENIUM", "TIMEOUT")
    else:
        TIMEOUT = 60


class NoseSelenium(Plugin):

    name = 'nose-selenium'
    score = 200
    status = {}

    def help(self):
        pass

    def _stringify_options(self, list):
        string = ", ".join(list)
        return "[" + string + "]"

    def options(self, parser, env=os.environ):

        Plugin.options(self, parser, env)
        parser.add_option('--config-file',
                          action='store',
                          dest='config_file',
                          help="Load options from ConfigParser compliant config file. " +
                               "Values in config file will override values sent on the " +
                               "command line."
        )
        parser.add_option('--browser',
                          action='store',
                          default=env.get('SELENIUM_BROWSER', 'FIREFOX'),
                          dest='browser',
                          help="Run this type of browser (default %default). " +
                               "run --browser-help for a list of what browsers are available. " +
                               "May be stored in environmental variable SELENIUM_BROWSER."
        )
        parser.add_option('--browser-help',
                          action='store_true',
                          dest='browser_help',
                          help="Get a list of what OS, BROWSER, and BROWSER_VERSION combinations are available."
        )
        parser.add_option('--build',
                          action='store',
                          dest='build',
                          default=None,
                          metavar='str',
                          help='build identifier (for continuous integration). ' +
                               'Only used for sauce.'
        )
        parser.add_option('--browser-version',
                          action='store',
                          type='str',
                          default="",
                          dest='browser_version',
                          help='Run this version of the browser. ' +
                               '(default: %default implies latest.)'
        )
        parser.add_option('--os',
                          action='store',
                          dest='os',
                          default=None,
                          help="Run the browser on this operating system. " +
                               "(default: %default, required for grid or sauce)"
        )
        parser.add_option('--timeout',
                          action='store',
                          type='int',
                          default=60,
                          metavar='num',
                          help='timeout (in seconds) for page loads, etc. ' +
                               '(default: %default)'
        )
        parser.add_option('--saved-files-storage',
                          action='store',
                          default=env.get('SAVED_FILES_PATH', ""),
                          dest='saved_files_storage',
                          metavar='PATH',
                          help='Full path to place to store screenshots and html dumps. ' +
                               'May be stored in environmental variable SAVED_FILES_PATH.'
        )

    def _check_validity(self, item, list, flag="--browser"):
        if item not in list:
            raise TypeError(
                "%s not in available options for %s: %s" %
                (item, flag, ", ".join(list))
            )

    @property
    def _valid_browsers_for_local(self):
        return ['FIREFOX', 'INTERNETEXPLORER', 'CHROME']

    def _browser_help(self):
        print("")
        print("Local Browsers:")
        print("---------------")
        print(("\n".join(self._valid_browsers_for_local)))
        exit(0)

    def ingest_config_file(self, config_file):
        CONFIG = ConfigParser()
        CONFIG.read(config_file)
        setup_selenium_from_config(CONFIG)

    def ingest_options(self, options):
        global BROWSER
        global BUILD
        global BROWSER_VERSION
        global OS
        global TIMEOUT

        BROWSER = options.browser
        TIMEOUT = options.timeout
        BUILD = options.build
        BROWSER_VERSION = options.browser_version
        OS = options.os
        SAVED_FILES_PATH = options.saved_files_storage

    def configure(self, options, conf):

        Plugin.configure(self, options, conf)
        if self.enabled:

            # browser-help is a usage call
            if getattr(options, 'browser_help'):
                self._browser_help()

            # get options from command line or config file
            if options.config_file:
                self.ingest_config_file(options.config_file)
            else:
                self.ingest_options(options)

            self._check_validity(BROWSER, self._valid_browsers_for_local)


class ScreenshotOnExceptionWebDriverWait(WebDriverWait):
    def __init__(self, *args, **kwargs):
        super(ScreenshotOnExceptionWebDriverWait, self).__init__(*args, **kwargs)
        global SAVED_FILES_PATH
        if SAVED_FILES_PATH:
          if not os.path.exists(SAVED_FILES_PATH):
            os.makedirs(SAVED_FILES_PATH)

    def until(self, *args, **kwargs):
        try:
            return super(
                ScreenshotOnExceptionWebDriverWait, self).until(
                *args, **kwargs)
        except TimeoutException:
            global SAVED_FILES_PATH
            if SAVED_FILES_PATH:
                timestamp = repr(time.time()).replace('.', '')
                # save a screenshot
                screenshot_filename = SAVED_FILES_PATH + "/" + timestamp + ".png"
                self._driver.get_screenshot_as_file(screenshot_filename)
                logger.error("Screenshot saved to %s" % screenshot_filename)
                # save the html
                html_filename = SAVED_FILES_PATH + "/" + timestamp + ".html"
                html = self._driver.page_source
                outfile = open(html_filename, 'w')
                outfile.write(html.encode('utf8', 'ignore'))
                outfile.close()
                logger.error("HTML saved to %s" % html_filename)
                logger.error("Page URL: %s" % self._driver.current_url)
            raise

    def until_not(self, *args, **kwargs):
        try:
            return super(
                ScreenshotOnExceptionWebDriverWait, self).until_not(
                *args, **kwargs)
        except TimeoutException:
            global SAVED_FILES_PATH
            if SAVED_FILES_PATH:
                timestamp = repr(time.time()).replace('.', '')
                # save a screenshot
                screenshot_filename = SAVED_FILES_PATH + "/" + timestamp + ".png"
                self._driver.get_screenshot_as_file(screenshot_filename)
                logger.error("Screenshot saved to %s" % screenshot_filename)
                # save the html
                html_filename = SAVED_FILES_PATH + "/" + timestamp + ".html"
                html = self._driver.page_source
                outfile = open(html_filename, 'w')
                outfile.write(html.encode('utf8', 'ignore'))
                outfile.close()
                logger.error("HTML saved to %s" % html_filename)
                logger.error("Page URL: %s" % self._driver.current_url)
            raise


class ScreenshotOnExceptionWebDriver(webdriver.Remote):


    def __init__(self, *args, **kwargs):
        super(ScreenshotOnExceptionWebDriver, self).__init__(*args, **kwargs)
        global SAVED_FILES_PATH
        if SAVED_FILES_PATH:
          if not os.path.exists(SAVED_FILES_PATH):
            os.makedirs(SAVED_FILES_PATH)

    def execute(self, driver_command, params=None):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe)
        if driver_command in [
            Command.SCREENSHOT,
            Command.GET_PAGE_SOURCE,
            Command.GET_CURRENT_URL
        ]:
            return super(ScreenshotOnExceptionWebDriver,
                             self).execute(driver_command, params=params)
        elif len(calframe) > 4 and calframe[4][3] in ['until', 'until_not']:
            return super(ScreenshotOnExceptionWebDriver,
                             self).execute(driver_command, params=params)
        else:
            try:
                return super(ScreenshotOnExceptionWebDriver,
                             self).execute(driver_command, params=params)
            except WebDriverException:
                global SAVED_FILES_PATH
                if SAVED_FILES_PATH:
                    timestamp = repr(time.time()).replace('.', '')
                    # save a screenshot
                    screenshot_filename = SAVED_FILES_PATH + "/" + timestamp + ".png"
                    self.get_screenshot_as_file(screenshot_filename)
                    logger.error("Screenshot saved to %s" % screenshot_filename)
                    # save the html
                    html_filename = SAVED_FILES_PATH + "/" + timestamp + ".html"
                    html = self.page_source
                    outfile = open(html_filename, 'w')
                    outfile.write(html.encode('utf8', 'ignore'))
                    outfile.close()
                    logger.error("HTML saved to %s" % html_filename)
                    logger.error("Page URL: %s" % self.current_url)
                raise



def build_webdriver(name="", tags=[], public=False):
    """Create and return the desired WebDriver instance."""
    global BROWSER
    global BUILD
    global BROWSER_VERSION
    global OS
    global TIMEOUT

    wd = None

    if BROWSER == 'FIREFOX':
        wd = webdriver.Firefox()
    elif BROWSER == 'CHROME':
        wd = webdriver.Chrome()
    elif BROWSER == 'INTERNETEXPLORER':
        wd = webdriver.Ie()
    else:
        raise TypeError(
            'WebDriver does not have a driver for local %s' % BROWSER)

    wd.implicitly_wait(TIMEOUT)
    # sometimes what goes out != what goes in, so log it
    logger.info("actual capabilities: %s" % wd.capabilities)
    return wd


class SeleniumTestCase(TestCase):

    def setUp(self):
        self.wd = build_webdriver()

    def tearDown(self):
        self.wd.quit()

