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

import io

import thriftpy2
from thriftpy2.rpc import make_server, make_client


# This is the Thrift input file as a string rather than a separate file. This
# allows the Thrift input to be contained within the module that's responsible
# for all Thrift-specific details rather than a separate .thrift file.
#
# thriftpy2 (https://github.com/Thriftpy/thriftpy2) is being used here instead
# of Apache Thrift since it offers an easier-to-use API exclusively for Python
# which is still compatible with servers/cleints using Apache Thrift (Apache
# Thrift can be used from a variety of different languages) while offering
# approximately the same performance.
#
# See the Apache Thrift tutorial for Python for examples:
# https://thrift.apache.org/tutorial/py.html
gaas_thrift_spec = """
# FIXME: consider additional, more fine-grained exceptions
exception GaasError {
  1:string message
}

struct Node2vecResult {
  1:list<i32> vertex_paths
  2:list<double> edge_weights
  3:list<i32> path_sizes
}

service GaasService {

  i32 uptime()

  i32 create_graph() throws(1:GaasError e),

  void delete_graph(1:i32 graph_id) throws (1:GaasError e),

  list<i32> get_graph_ids() throws(1:GaasError e),

  void load_csv_as_vertex_data(1:string csv_file_name,
                               2:string delimiter,
                               3:list<string> dtypes,
                               4:i32 header,
                               5:string vertex_col_name,
                               6:string type_name,
                               7:list<string> property_columns,
                               8:i32 graph_id
                               ) throws (1:GaasError e),

  void load_csv_as_edge_data(1:string csv_file_name,
                             2:string delimiter,
                             3:list<string> dtypes,
                             4:i32 header,
                             5:list<string> vertex_col_names,
                             6:string type_name,
                             7:list<string> property_columns,
                             8:i32 graph_id
                             ) throws (1:GaasError e),

  i32 get_num_edges(1:i32 graph_id) throws(1:GaasError e),

  Node2vecResult
  node2vec(1:list<i32> start_vertices,
           2:i32 max_depth,
           3:i32 graph_id
           ) throws (1:GaasError e),

  i32 extract_subgraph(1:string create_using,
                       2:string selection,
                       3:string edge_weight_property,
                       4:double default_edge_weight,
                       5:bool allow_multi_edges,
                       6:i32 graph_id
                       ) throws (1:GaasError e),

  i32 load_graph_creation_extensions(1:string extension_dir_path
                                     ) throws (1:GaasError e),

  void unload_graph_creation_extensions(),

  i32 call_graph_creation_extension(1:string func_name,
                                    2:string func_args_repr,
                                    3:string func_kwargs_repr
                                    ) throws (1:GaasError e),
}
"""

# Load the GaaS Thrift specification on import. Syntax errors and other problems
# will be apparent immediately on import, and it allows any other module to
# import this and access the various types define in the Thrift specification
# without being exposed to the thriftpy2 API.
spec = thriftpy2.load_fp(io.StringIO(gaas_thrift_spec),
                         module_name="gaas_thrift")

def create_server(handler, host, port):
    """
    Return a server object configured to listen on host/port and use the handler
    object to handle calls from clients. The handler object must have an
    interface compatible with the GaasService service defined in the Thrift
    specification.

    Note: This function is defined here in order to allow it to have easy access
    to the Thrift spec loaded here on import, and to keep all thriftpy2 calls in
    this module. However, this function is likely only called from the
    gaas_server package which depends on the code in this package.
    """
    return make_server(spec.GaasService, handler, host, port)


def create_client(host, port, call_timeout=90000):
    """
    Return a client object that will make calls on a server listening on
    host/port.

    The call_timeout value defaults to 90 seconds, and is used for setting the
    timeout for server API calls when using the client created here - if a call
    does not return in call_timeout milliseconds, an exception is raised.
    """
    try:
        return make_client(spec.GaasService, host=host, port=port,
                           timeout=call_timeout)
    except thriftpy2.transport.TTransportException:
        # Rasie a GaaS exception in order to completely encapsulate all Thrift
        # details in this module. If this was not done, callers of this function
        # would have to import thriftpy2 in order to catch the
        # TTransportException, which then leaks thriftpy2.
        #
        # NOTE: normally the GaasError exception is imported from the
        # gaas_client.exceptions module, but since
        # gaas_client.exceptions.GaasError is actually defined from the spec in
        # this module, just use it directly from spec.
        #
        # FIXME: this exception could use more detail
        raise spec.GaasError("could not create a client session with a "
                             "GaaS server")
