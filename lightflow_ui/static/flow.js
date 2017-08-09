function get_color(d) {
    // colours from http://clrs.cc/
    var colours = {
        'SUCCESS': '#2ECC40',
        'LIGHTFLOW-STARTED': '#FF851B'
    }
    if (colours[d.state]) {
        return colours[d.state];
    }
    console.log(d.state);
    return 'pink';
}

function render_graph(links, nodes, locations, statuses) {
    var get_loc = (size, key) => name => (
        locations[name][key] * size * spacing_factor
    )

    var node_height = 40,
        node_width = 200,
        graph_height = 1024,
        graph_width = 1024,
        spacing_factor = 1.1;

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
        .attr('stroke', get_color)
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
            .attr('stroke', get_color)
            .attr('fill', get_color)
            .attr(
                'transform',
                d => (
                    // move the text somewhere nice
                    `translate(` +
                        `${get_x(d.name) + 2.5},` +
                        `${get_y(d.name) + 14}` +
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
