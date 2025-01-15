"""
################################################################################
Function: summary_utils.py
Purpose: Utility functions for creating summaries and visualizations of the 
         package hierarchy and resource relationships.
Authors: Sebastian Steinig
Version History:
    - 1.0 (2024-02): Initial creation of the function.
################################################################################
"""

import os
import json
import graphviz
from collections import defaultdict

def create_dependency_graph(package_summaries, output_dir):
    """Create a visual dependency graph using graphviz."""
    # Create a new directed graph
    dot = graphviz.Digraph(comment='Package Hierarchy')
    dot.attr(rankdir='TB')  # Top to bottom layout
    
    # Set global node attributes
    dot.attr('node', 
            fontname='Arial',
            fontsize='10',
            width='2',
            height='0.5',
            margin='0.2')
    
    # Create invisible nodes for better alignment
    with dot.subgraph(name='column_headers') as h:
        h.attr(rank='same')
        h.node('packages_header', 'Packages', shape='none', fontsize='16', fontweight='bold')
        h.node('products_header', 'Products', shape='none', fontsize='16', fontweight='bold')
        h.node('layers_header', 'Layers', shape='none', fontsize='16', fontweight='bold')
        h.node('styles_header', 'Styles', shape='none', fontsize='16', fontweight='bold')
        h.edge('packages_header', 'products_header', style='invis')
        h.edge('products_header', 'layers_header', style='invis')
        h.edge('layers_header', 'styles_header', style='invis')
    
    # Add nodes and edges for each package
    for package_name, summary in package_summaries.items():
        # Add package node
        package_id = f"package_{package_name}"
        dot.node(package_id, 
                f"{package_name}\\n({summary['title']})", 
                shape='folder',
                style='filled',
                fillcolor='#ADD8E6',
                fontcolor='black')
        
        # Group products by type
        products_by_type = defaultdict(list)
        for product_name, product_info in summary['products'].items():
            products_by_type[product_info['type']].append((product_name, product_info))
        
        # Process each product type
        for product_type in ['single', 'grouped']:
            if product_type in products_by_type:
                # Create a subgraph for this product type to keep products together
                with dot.subgraph(name=f'cluster_{package_name}_{product_type}') as s:
                    s.attr(rank='same')  # Keep products at same rank
                    
                    for product_name, product_info in sorted(products_by_type[product_type]):
                        # Add product node with wrapped label
                        product_id = f"product_{product_name}"
                        wrapped_name = "\\n".join(product_name.split('-'))
                        s.node(product_id,
                              wrapped_name,
                              shape='box',
                              style='filled',
                              fillcolor='#90EE90',
                              fontcolor='black')
                        dot.edge(package_id, product_id)
                        
                        # Create a subgraph for this product's layers and styles
                        with dot.subgraph(name=f'cluster_{product_name}_resources') as p:
                            # Add layer nodes
                            prev_layer_id = None
                            for layer in product_info['layers']:
                                layer_id = f"layer_{layer}"
                                wrapped_layer = "\\n".join(layer.split('_'))
                                p.node(layer_id,
                                     wrapped_layer,
                                     shape='box',
                                     style='filled',
                                     fillcolor='#FFFFE0',
                                     fontcolor='black')
                                dot.edge(product_id, layer_id)
                                if prev_layer_id:
                                    p.edge(prev_layer_id, layer_id, style='invis')
                                prev_layer_id = layer_id
                            
                            # Add style nodes
                            prev_style_id = None
                            for style in product_info['styles']:
                                style_id = f"style_{style}"
                                wrapped_style = "\\n".join(style.split('_'))
                                p.node(style_id,
                                     wrapped_style,
                                     shape='box',
                                     style='filled',
                                     fillcolor='#FFB6C1',
                                     fontcolor='black')
                                dot.edge(product_id, style_id)
                                if prev_style_id:
                                    p.edge(prev_style_id, style_id, style='invis')
                                prev_style_id = style_id
    
    # Save the graph
    graph_file = os.path.join(output_dir, "package_hierarchy")
    dot.render(graph_file, format='png', cleanup=True)
    print(f"\nDependency graph saved to: {graph_file}.png")

def create_summary(package_summaries, output_dir):
    """Create text and JSON summaries of all created resources and their relationships."""
    def print_indented(text, level=0):
        indent = "  " * level
        return f"{indent}{text}"

    # Collect all unique layers and styles
    all_layers = {layer for summary in package_summaries.values() 
                 for product in summary['products'].values() 
                 for layer in product['layers']}
    all_styles = {style for summary in package_summaries.values() 
                 for product in summary['products'].values() 
                 for style in product['styles']}

    # Prepare summary text
    summary_lines = []
    summary_lines.append("="*80)
    summary_lines.append("CREATION SUMMARY")
    summary_lines.append("="*80)
    summary_lines.append("Total resources created:")
    summary_lines.append(f"  - Packages: {len(package_summaries)}")
    summary_lines.append(f"  - Products: {sum(len(summary['products']) for summary in package_summaries.values())}")
    summary_lines.append(f"  - Layers: {len(all_layers)}")
    summary_lines.append(f"  - Styles: {len(all_styles)}")
    
    summary_lines.append("\nCreated Layers:")
    summary_lines.append("="*80)
    for layer in sorted(all_layers):
        summary_lines.append(f"  - {layer}")
    
    summary_lines.append("\nCreated Styles:")
    summary_lines.append("="*80)
    for style in sorted(all_styles):
        summary_lines.append(f"  - {style}")

    summary_lines.append("\nResource hierarchy:")
    summary_lines.append("="*80)
    for package_name, summary in package_summaries.items():
        summary_lines.append(print_indented(f"📦 Package: {package_name} ({summary['title']})"))
        
        # Group products by type (single/grouped)
        products_by_type = defaultdict(list)
        for product_name, product_info in summary['products'].items():
            products_by_type[product_info['type']].append((product_name, product_info))

        # Print single products
        if 'single' in products_by_type:
            summary_lines.append(print_indented("📋 Single Products:", 1))
            for product_name, product_info in sorted(products_by_type['single']):
                summary_lines.append(print_indented(f"- {product_name}", 2))
                summary_lines.append(print_indented("Layers:", 3))
                for layer in product_info['layers']:
                    summary_lines.append(print_indented(f"- {layer}", 4))
                summary_lines.append(print_indented("Styles:", 3))
                for style in product_info['styles']:
                    summary_lines.append(print_indented(f"- {style}", 4))

        # Print grouped products
        if 'grouped' in products_by_type:
            summary_lines.append(print_indented("📋 Grouped Products:", 1))
            for product_name, product_info in sorted(products_by_type['grouped']):
                summary_lines.append(print_indented(f"- {product_name}", 2))
                summary_lines.append(print_indented("Layers:", 3))
                for layer in product_info['layers']:
                    summary_lines.append(print_indented(f"- {layer}", 4))
                summary_lines.append(print_indented("Styles:", 3))
                for style in product_info['styles']:
                    summary_lines.append(print_indented(f"- {style}", 4))

    # Print summary to console
    print("\n".join(summary_lines))

    # Save human-readable summary to text file
    summary_file = os.path.join(output_dir, "creation_summary.txt")
    with open(summary_file, "w") as f:
        f.write("\n".join(summary_lines))
    print(f"\nSummary saved to: {summary_file}")

    # Save machine-readable summary to JSON file
    json_summary = {
        "statistics": {
            "packages": len(package_summaries),
            "products": sum(len(summary['products']) for summary in package_summaries.values()),
            "layers": len(all_layers),
            "styles": len(all_styles)
        },
        "resources": {
            "layers": sorted(list(all_layers)),
            "styles": sorted(list(all_styles))
        },
        "packages": package_summaries
    }
    json_summary_file = os.path.join(output_dir, "creation_summary.json")
    with open(json_summary_file, "w") as f:
        json.dump(json_summary, f, indent=2, sort_keys=True)
    print(f"JSON summary saved to: {json_summary_file}")

    # Create visual dependency graph
    create_dependency_graph(package_summaries, output_dir) 