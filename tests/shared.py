"""
This file contains shared functions and variables used within multiple tests.

Author(s): David Marchant
"""
import os

from core.functionality import make_dir, rmtree


# testing 
TEST_MONITOR_BASE = "test_monitor_base"
TEST_HANDLER_BASE = "test_handler_base"
TEST_JOB_OUTPUT = "test_job_output"

def setup():
    make_dir(TEST_MONITOR_BASE, ensure_clean=True)
    make_dir(TEST_HANDLER_BASE, ensure_clean=True)
    make_dir(TEST_JOB_OUTPUT, ensure_clean=True)

def teardown():
    rmtree(TEST_MONITOR_BASE)
    rmtree(TEST_HANDLER_BASE)
    rmtree(TEST_JOB_OUTPUT)
    rmtree("first")

# Recipe funcs
BAREBONES_PYTHON_SCRIPT = [
    ""
]
COMPLETE_PYTHON_SCRIPT = [
    "import os",
    "# Setup parameters",
    "num = 1000",
    "infile = 'somehere"+ os.path.sep +"particular'",
    "outfile = 'nowhere"+ os.path.sep +"particular'",
    "",
    "with open(infile, 'r') as file:",
    "    s = float(file.read())",
    ""
    "for i in range(num):",
    "    s += i",
    "",
    "div_by = 4",
    "result = s / div_by",
    "",
    "print(result)",
    "",
    "os.makedirs(os.path.dirname(outfile), exist_ok=True)",
    "",
    "with open(outfile, 'w') as file:",
    "    file.write(str(result))",
    "",
    "print('done')"
]

# Jupyter notebooks
BAREBONES_NOTEBOOK = {
    "cells": [],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 4
}
COMPLETE_NOTEBOOK = {
 "cells": [
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": "# The first cell\n\ns = 0\nnum = 1000"
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": "for i in range(num):\n    s += i"
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": "div_by = 4"
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": "result = s / div_by"
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": "print(result)"
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
APPENDING_NOTEBOOK = {
 "cells": [
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Default parameters values\n",
    "# The line to append\n",
    "extra = 'This line comes from a default pattern'\n",
    "# Data input file location\n",
    "infile = 'start"+ os.path.sep +"alpha.txt'\n",
    "# Output file location\n",
    "outfile = 'first"+ os.path.sep +"alpha.txt'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# load in dataset. This should be a text file\n",
    "with open(infile) as input_file:\n",
    "    data = input_file.read()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Append the line\n",
    "appended = data + '\\n' + extra"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "\n",
    "# Create output directory if it doesn't exist\n",
    "output_dir_path = os.path.dirname(outfile)\n",
    "\n",
    "if output_dir_path:\n",
    "    os.makedirs(output_dir_path, exist_ok=True)\n",
    "\n",
    "# Save added array as new dataset\n",
    "with open(outfile, 'w') as output_file:\n",
    "   output_file.write(appended)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.10.6 (main, Nov 14 2022, 16:10:14) [GCC 11.3.0]"
  },
  "vscode": {
   "interpreter": {
    "hash": "916dbcbb3f70747c44a77c7bcd40155683ae19c65e1c03b4aa3499c5328201f1"
   }
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
ADDING_NOTEBOOK = {
 "cells": [
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Default parameters values\n",
    "# Amount to add to data\n",
    "extra = 10\n",
    "# Data input file location\n",
    "infile = 'example_data"+ os.path.sep +"data_0.npy'\n",
    "# Output file location\n",
    "outfile = 'standard_output"+ os.path.sep +"data_0.npy'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import numpy as np\n",
    "import os"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# load in dataset. Should be numpy array\n",
    "data = np.load(infile)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Add an amount to all the values in the array\n",
    "added = data + int(float(extra))\n",
    "\n",
    "added"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Create output directory if it doesn't exist\n",
    "output_dir_path = os.path.dirname(outfile)\n",
    "\n",
    "if output_dir_path:\n",
    "    os.makedirs(output_dir_path, exist_ok=True)\n",
    "\n",
    "# Save added array as new dataset\n",
    "np.save(outfile, added)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.6.9"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
