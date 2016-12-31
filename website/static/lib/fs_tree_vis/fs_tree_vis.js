// Given a json represented *merged* filesystem status, and a div id to draw the visualization,
// render the visualization there.
// The filesystem json should be one created from fs_diff.py
function build_fs_tree_vis(data, div_id) {

    var init_time = true;
    var id = 0;

    var tree = d3.layout.treelist()
        .childIndent(15)
        .nodeHeight(22);
    var ul = d3.select(div_id).append("ul").classed("treelist", "true");

    function render(data, parent) {
        var nodes = tree.nodes(data),
            duration = 250;
        function toggleChildren(d) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else if (d._children) {
                d.children = d._children;
                d._children = null;
            }
        }

        var nodeEls = ul.selectAll("li.node").data(nodes, function (d) {
            d.id = d.id || ++id;
            return d.id;
        });
        //entered nodes
        var entered = nodeEls.enter().append("li").classed("node", true)
            .style("top", parent.y +"px")
            .style("opacity", 0)
            .style("height", tree.nodeHeight() + "px")
            .on("click", function (d) {
                toggleChildren(d);
                render(data, d);
            })
            .on("mouseover", function (d) {
                d3.select(this).classed("selected", true);
            })
            .on("mouseout", function (d) {
                d3.selectAll(".selected").classed("selected", false);
            });
            
        //add arrows if it is a folder
        entered.append("span").attr("class", function (d) {
            var icon = d.children ? " glyphicon-chevron-down"
                : d._children ? "glyphicon-chevron-right" : "";
            return "caret glyphicon " + icon;
        });
        //add icons for folder for file
        entered.append("span").attr("class", function (d) {
            var icon = d.children || d._children ? "glyphicon-folder-close"
                : "glyphicon-file";
            return "glyphicon " + icon;
        });

        ul.selectAll("li.node").style("color", function(d) {
            if (d.tag.hasOwnProperty("extra"))
                return "red";
        });

        //add text
        entered.append("span").attr("class", "filename")
            .html(function (d) { return d.name; });
        //update caret direction
        nodeEls.select("span.caret").attr("class", function (d) {
            var icon = d.children ? " glyphicon-chevron-down"
                : d._children ? "glyphicon-chevron-right" : "";
            return "caret glyphicon " + icon;
        });
        //update position with transition
        nodeEls.transition().duration(duration)
            .style("top", function (d) { return (d.y - tree.nodeHeight()) + "px";})
            .style("left", function (d) { return d.x + "px"; })
            .style("opacity", function (d) {
                    if (d.tag.hasOwnProperty("missing"))
                        return 0.3;
                    else 
                        return 1;
                }
            );
        nodeEls.exit().remove();
    }

    render(data, data);

    // collapse the directory if it is the top level non-modified field
    if (init_time) {
        d3.select("body").selectAll("li.node").each(function(d, i) {
            if (d.tag == "higest_non_modified") {
                var onClickFunc = d3.select(this).on("click");
                onClickFunc.apply(this, [d, i]);
            }
        });
        init_time = false;
    }
}
