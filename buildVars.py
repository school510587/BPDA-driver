# -*- coding: UTF-8 -*-

# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

# Full getext (please don't change)
_ = lambda x : x

# Add-on information variables
addon_info = {
    # for previously unpublished addons, please follow the community guidelines at:
    # https://bitbucket.org/nvdaaddonteam/todo/raw/master/guidelines.txt
    # add-on Name, internal for nvda
    "addon_name" : "seikamini",
    # Add-on summary, usually the user visible name of the addon.
    # Translators: Summary for this add-on to be shown on installation and add-on information.
    "addon_summary" : _("Seika notetakers driver for Mini16, Mini24, V6 & V7"),
    # Add-on description
    # Translators: Long description to be shown for this add-on on add-on information from add-ons manager
    "addon_description" : _("""Repackaging by Accessolutions of the driver\nprovided by the manufacturer as an NVDA add-on."""),
    # Version
    "addon_version" : "3.3.2024.3",
    # Author(s)
    "addon_author" : u"Accessolutions <contact@accessolutions.fr>, Tsinghua Univ., Ulf Beckmann <beckmann@flusoft.de>, Bo-Cheng Jhan <school510587@yahoo.com.tw>",
    # URL for the add-on documentation support
    "addon_url" : "http://www.nippontelesoft.com/english.html",
    # Documentation file name
    "addon_docFileName" : "readme.html",
    # Minimum NVDA version supported (e.g. "2018.3.0", minor version is optional)
    "addon_minimumNVDAVersion" : "2022.1",
    # Last NVDA version supported/tested (e.g. "2018.4.0", ideally more recent than minimum version)
    "addon_lastTestedNVDAVersion" : "2024.3",
    # Add-on update channel (default is stable or None)
    "addon_updateChannel" : None,
}


import os.path

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = [
    "addon/brailleDisplayDrivers/*.py",
]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles = []
