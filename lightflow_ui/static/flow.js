function render_graph(links, nodes, locations, statuses) {
    function get_color(d) {
        // colours from http://clrs.cc/
        var state = statuses[d.name];
        var colours = {
            'SUCCESS': 'green',
            'STOPPED': 'aqua',
            'ABORTED': 'blue',
            'ERROR': 'red',
            'LIGHTFLOW-STARTED': 'orange',
            'NOT-RUNNING': 'navy'
        }
        if (colours[state]) {
            return colours[state];
        }
        console.log(state);
        return '#F012BE';
    }
    function color_for() {
        return d => (
            Array.prototype.slice.call(arguments)
            .map(
                type => type + get_color(d)
            )
            .join(' ')
        )
    }

    var get_loc = (size, key) => name => (
        5 + (locations[name][key] * size * spacing_factor)
    )

    var node_height = 40,
        node_width = 200,
        graph_height = 1024,
        graph_width = 1024,
        spacing_factor = 1.1,
        text_size = 19.2;

    var svg = d3.select('svg')
        .attr('width', graph_width)
        .attr('height', graph_height);

    var domain = [
        d3.min(nodes, d => d.received),
        d3.max(nodes, d => d.succeeded)
    ]
    var scale = d3.scale.linear()
        .domain(domain)
        .range([0, svg.attr('width')])

    var get_x = get_loc(node_width, 'column');
    var get_y = get_loc(node_height, 'row');

    var g = svg.selectAll('g').data(nodes)
    g.enter()
        .append('rect')
        .attr('width', node_width)
        .attr('height', node_height)
        .attr('class', color_for('stroke-'))
        .attr('fill', 'white')
        .attr(
            'transform',
            d => (
                `translate(${get_x(d.name)}, ${get_y(d.name)})`
            )
        );
    g.enter()
        .append('text')
            .text(d => d.name)
            .attr('class', color_for('stroke-', 'fill-'))
            .attr('font-size', `${text_size}px`)
            .attr(
                'transform',
                d => (
                    // move the text somewhere nice
                    `translate(` +
                        `${get_x(d.name) + 8},` +
                        `${
                            get_y(d.name) +
                            (node_height / 2) +
                            (text_size / 4)
                        }` +
                    `)`
                )
            );

    function get_y_for_link(name) {
        return get_y(name) + (node_height / 2);
    }

    svg.attr('class', 'line')
        .selectAll('line').data(links)
        .enter().append('line')
        .style('stroke', 'grey')

        .attr('x1', d => get_x(d.source) + node_width)
        .attr('y1', d => get_y_for_link(d.source))

        .attr('x2', d => get_x(d.target))
        .attr('y2', d => get_y_for_link(d.target));
}
