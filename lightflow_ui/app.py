import json
from pathlib import Path
from operator import attrgetter
from collections import defaultdict

import tornado.web
import tornado.ioloop
import networkx as nx
import flower.api.events  # noqa
from flower.events import Events
from lightflow.config import Config
from lightflow.queue.app import create_app
from tornado.options import parse_command_line
from lightflow.models.datastore import DataStore
from flower.utils.tasks import iter_tasks, get_task_by_id
from lightflow.models.exceptions import DataStoreDecodeUnknownType


class Flower:
    def __init__(self, events):
        self.events = events

    def task_info(self, uuid):
        # return requests.get(self.root + '/task/info/' + uuid).json()
        return get_task_by_id(uuid).as_dict()

    def tasks(self):
        return dict(iter_tasks(self.events))

    def roots(self, tasks=None):
        return [
            task
            for task_id, task in (tasks or self.tasks()).items()
            if task == task.root
        ]

    def currently_running(self, tasks=None):
        for root in self.roots(tasks):
            any_not_finished = any(
                task.state != 'SUCCESS'
                for task in grab_related(tasks, root)
            )

            if any_not_finished:
                yield root


def grab_related(tasks, curr):
    """
    Grabs all the related tasks
    """
    for task in tasks.values():
        if curr.root == task.root:
            yield task


def parse_args(args):
    args = args[1:-1].split(', ')

    for arg in args:
        if arg[0] == arg[-1] == "'":
            yield arg[1:-1]
        else:
            yield arg


def get_workflow_id(related_tasks):
    task_args = [
        list(parse_args(task.args))
        for task in related_tasks
    ]
    return next(
        args[1]
        for args in task_args
        if len(args) == 3
    )


def calculate_locations(graph):
    root_node = next(
        node
        for node in graph.nodes()
        if len(graph.predecessors(node)) == 0
    )
    undirected = graph.to_undirected()

    buckets = defaultdict(list)
    for node in graph.nodes():
        distance = nx.shortest_path_length(
            undirected,
            root_node,
            node
        )

        buckets[distance].append(node)

    return {
        node.name: {
            'column': col_idx,
            'row': row_idx
        }
        for col_idx, column in buckets.items()
        for row_idx, node in enumerate(sorted(column, key=attrgetter('name')))
    }


def determine_statuses(graph, related):
    # nodes in the graph that weren't run (or have not yet run) won't appear
    # in the list of related tasks
    statuses = dict.fromkeys(
        (node.name for node in graph.nodes()),
        'NOT-RUNNING'
    )
    for task in related:
        statuses[task.name] = task.state
    return statuses


class ForUUIDHandler(tornado.web.RequestHandler):
    def get(self, uuid):
        tasks = self.application.flower.tasks()

        try:
            root = tasks[uuid]
        except KeyError:
            return self.render(
                'flow_not_found.html',
                uuid=uuid
            )
        else:
            related = list(grab_related(tasks, root))


        workflow_id = get_workflow_id(related)

        workflow = self.application.data_store.get(workflow_id)

        try:
            workflow_name = workflow.get('name', section='meta')
        except DataStoreDecodeUnknownType:
            return self.render(
                'cannot_retrieve_workflow.html',
                workflow_id=workflow_id
            )

        dag = workflow.get('dag', section='data')
        graph = dag.make_graph(dag._schema)

        # location data to lay out the graph
        locations = calculate_locations(graph)

        # the links for d3 to consume
        connections = [
            {
                "source": source.name,
                "target": target.name
            }
            for source, target in graph.edges()
        ]

        statuses = determine_statuses(graph, related)

        self.render(
            'flow.html',
            **{
                'tasks': tasks,
                'related': related,
                'statuses': statuses,
                'connections': connections,
                'locations': locations,
                'json': json
            }
        )


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        tasks = self.application.flower.tasks()

        self.render(
            'index.html',
            roots=self.application.flower.roots(tasks),
            currently_running=list(self.application.flower.currently_running(tasks))
        )


def main():
    parse_command_line()

    config = Config.from_file(
        '/mnt/c/Users/me/Documents/Lightflow/lightflow.cfg'
    )

    io_loop = tornado.ioloop.IOLoop().current()

    here = Path(__file__).parent
    settings = {
        'static_path': str(here / 'static'),
        'template_path': str(here / 'templates'),
        'debug': True,
        'autoreload': True
    }

    tornado_app = tornado.web.Application(
        [
            (
                (r'/flow/(?P<uuid>[^/]*)'),
                ForUUIDHandler,
                {},
                'for_uuid'
            ),
            (
                (r'/'),
                IndexHandler,
                {},
                'index'
            ),
            (
                r'/static/(.*)',
                tornado.web.StaticFileHandler,
                {'path': settings['static_path']}
            ),
        ],
        **settings
    )
    tornado_app.events = Events(
        create_app(config),
        io_loop=io_loop,
        persistent=True,
        db='deebee'
    )
    tornado_app.data_store = DataStore(
       auto_connect=True,
       **config.data_store
    )
    tornado_app.flower = Flower(tornado_app.events)

    tornado_app.events.start()
    tornado_app.listen(8888)

    io_loop.start()


if __name__ == '__main__':
    main()
