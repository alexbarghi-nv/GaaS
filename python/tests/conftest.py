# Copyright (c) 2022, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

graph_creation_extension_file_contents = """
import cudf
from cugraph.experimental import PropertyGraph

def __my_private_function():
   pass

def my_graph_creation_function(arg1, arg2):
   edgelist = cudf.DataFrame(columns=[arg1, arg2], data=[(0,1), (88,99)])
   pG = PropertyGraph()
   pG.add_edge_data(edgelist, vertex_col_names=(arg1, arg2))
   return pG
"""

@pytest.fixture
def graph_creation_extension():

    with TemporaryDirectory() as tmp_extension_dir:
        # write graph creation extension .py file
        graph_creation_extension_file = open(
            Path(tmp_extension_dir)/"my_graph_creation_extension.py",
            "w")
        print(graph_creation_extension_file_contents,
              file=graph_creation_extension_file,
              flush=True)

        yield tmp_extension_dir
