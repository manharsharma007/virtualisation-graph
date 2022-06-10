var width = 1000,
height = 760;

function interactive_graph(edges = true, simulate = true) {
    d3.select('#svg').selectAll('*').remove();
    d3.select('body').select('.tooltip').remove();
    var svg = d3.select("#svg").select("svg")
    if (svg.empty()) {
        svg = d3.select("#svg").append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .call(d3.zoom().on("zoom", function () {
                       svg.attr("transform", d3.event.transform)
                    })).append("g");
    }

    var color = d3.scaleOrdinal(d3.schemeCategory20);

    var div = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    var simulation = d3.forceSimulation();
    if(edges) {
        simulation
            .force("link", d3.forceLink().id(function(d) { return d.id; }));
    }

    d3.json("static/assets/uploads/graph.json", function(error, graph) {
      if (error) throw error;
      var edge_color = graph.edges;
      var font_color = graph.font_color;
      var d_labels = graph.d_labels;
      var fixed_n = graph.fixed_n;
      var pos = JSON.parse(graph.pos);

      if(edges) {

          var link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graph.links)
            .enter().append("line")
            .attr("stroke-width", function(d) { return Math.sqrt(d.value); })
            .attr("stroke", edge_color);
        }

      var node_ = svg.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(graph.nodes)
      .enter().append("g")
        .on("mouseover", mouseOver(0.2))
        .on("mouseout", mouseOut)
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

    
      var node = node_.append("circle")
      .attr("r", scaledSize)
        .attr("fill", function(d) { return d.color; })

      if(d_labels) {
        var lables = node_.append("text")
        .text(function(d) {
          return d.id;
        }).attr("fill", font_color);

        node_.append("title")
        .text(function(d) { return d.id; });
      }

      if(simulate == true) {
        simulation.force("charge", d3.forceManyBody())
              .force("center", d3.forceCenter(width / 2, height / 2))
          .nodes(graph.nodes)
          .on("tick", ticked);

        if(edges) {
          simulation.force("link")
            .links(graph.links);
        }
      }
        else {
          simulation.nodes(graph.nodes).force("center", d3.forceCenter(width / 2, height / 2))
            .on("tick", ticked);

          if(edges) {
            simulation.force("link")
              .links(graph.links).strength(0);
          }
        }

      svg.selectAll("circle").on("click", function(d){

        $.selectNode(d.id);

        let name = "Nodes: " + d.id.toUpperCase();
        let string = "Neighbours: ";

        Object.keys(linkedByIndex[d.index]).forEach(key => {
          for(n of graph.nodes) {
            if(n.index == key && n.id != undefined) {
              string += (n.id.toUpperCase() + ", ");
            }
          }
        });

        let f_nodes = document.getElementById("Nodes");
        f_nodes.innerHTML = name;

        let f_neighbours = document.getElementById("Neighbours");
        f_neighbours.innerHTML = string;

      });

      function ticked() {
        if(edges) {
            link
              .attr("x1", function(d) { return d.source.x; })
              .attr("y1", function(d) { return d.source.y; })
              .attr("x2", function(d) { return d.target.x; })
              .attr("y2", function(d) { return d.target.y; });
          }
        node_
          .attr("transform", function(d) {
          return "translate(" + d.x + "," + d.y + ")";
        })
        if(d_labels){
          lables.attr('x', function(d) { return (d.degree + 5); })
            .attr('y', function(d) { return (d.degree + 3); });
          }
      }

      var linkedByIndex = {};
      var nodeDegrees = {};

      graph.links.forEach(function(d) {
        if(d.source.index in linkedByIndex) {
          linkedByIndex[d.source.index][d.target.index] = 1;
        } else {
          let val = {};
          val[d.target.index] = 1;
          linkedByIndex[d.source.index] =  val;
        }

        if(d.source.index in nodeDegrees) {
          let val = nodeDegrees[d.source.index];
          nodeDegrees[d.source.index] = (val + 1);
        } else {
          nodeDegrees[d.source.index] = 1;
        }



        // for undirected graphs


        if(d.target.index in linkedByIndex) {
          linkedByIndex[d.target.index][d.source.index] = 1;
        } else {
          let val = {};
          val[d.source.index] = 1;
          linkedByIndex[d.target.index] =  val;
        }

        if(d.target.index in nodeDegrees) {
          let val = nodeDegrees[d.target.index];
          nodeDegrees[d.target.index] = (val + 1);
        } else {
          nodeDegrees[d.target.index] = 1;
        }


      });

      function isConnected(a, b) {
        if (linkedByIndex[a.index][b.index] == 1) {
          return 1;
        }
      }

      function scaledSize(d) {
        if(fixed_n) {
          return 7;
        }

        if(d.degree > 100) {
            c_ = 0.3
        }
        else if(d.degree < 10) {
            c_ = 1.5;
        }
        else
            c_ = 0.8;
        return d.degree * c_ + 0.3;
      }

      function mouseOver(opacity) {
        return function(d) {
            // check all other nodes to see if they're connected
            // to this one. if so, keep the opacity at 1, otherwise
            // fade
            div.transition()
              .duration(200)
              .style("opacity", .9);

            div.html(d.id)
              .style("left", (d3.event.pageX) + "px")
              .style("top", (d3.event.pageY - 28) + "px");

            node.style("fill-opacity", function(o) {
              
              thisOpacity = (isConnected(d, o) || d === o) ? 1 : opacity;
              $(this).siblings().css("fill-opacity", thisOpacity);
              return thisOpacity;
            });
            // also style link accordingly
            
                link.style("stroke-opacity", function(o) {
                  return (o.source === d || o.target === d) ? 1 : opacity;
                });

                link.style("stroke", function(o){
                  if(o.source === d){
                    return o.target.color;
                  }
                  else if(o.target === d){
                    return o.source.color;
                  }
                  else{
                    return edge_color;
                  }
                });


            //node.style("stroke-opacity", function(o) {
            //     thisOpacity = isConnected(d, o) ? 1 : opacity;
            //     return thisOpacity;
            // });
            // node.style("fill-opacity", function(o) {
            //     thisOpacity = isConnected(d, o) ? 1 : opacity;
            //     return thisOpacity;
            // });
            // // also style link accordingly
            // link.style("stroke-opacity", function(o) {
            //     return o.source === d || o.target === d ? 1 : opacity;
            // });
            // link.style("stroke", function(o){
            //     return o.source === d || o.target === d ? o.source.color : "#ddd";
            // });
        };
      }

      function mouseOut() {
          div.transition()
            .duration(500)
            .style("opacity", 0);

          node.style("stroke-opacity", 1);
          node.style("fill-opacity", 1);
          if(d_labels) {
            lables.style("fill-opacity", 1);
          }

          if(edges) {
              link.style("stroke-opacity", 1);
              link.style("stroke", edge_color);
              link.style("stroke-width", 1);
          }
      }
    });

    function dragstarted(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(d) {
      d.fx = d3.event.x;
      d.fy = d3.event.y;
    }

    function dragended(d) {
      if (!d3.event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
}