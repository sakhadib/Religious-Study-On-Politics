#!/usr/bin/env python3
"""
Political Compass Plotter
Plots religious/philosophical perspectives on a 2D political compass
X-axis: Economic (Left-Right), Y-axis: Social (Libertarian-Authoritarian)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.lines import Line2D
from pathlib import Path

def create_political_compass_plot(csv_file: str = "_pc_scores.csv", output_file: str = "political_compass.png"):
    """
    Create a political compass scatter plot
    
    Args:
        csv_file: Path to the CSV file with religion, econ_score, soc_score
        output_file: Output image file path
    """
    
    # Read the data
    print(f"📖 Reading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    
    print(f"✅ Loaded {len(df)} religions/beliefs")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Define quadrant colors (using light colors)
    quadrant_colors = {
        1: '#ADD8E6',  # Light blue (Right-Authoritarian)
        2: '#FFB6C1',  # Light red (Left-Authoritarian) 
        3: '#90EE90',  # Light green (Left-Libertarian)
        4: '#DDA0DD'   # Light purple (Right-Libertarian)
    }
    
    # Create quadrant backgrounds
    # Quadrant 1: Right-Authoritarian (x: pos, y: pos)
    rect1 = patches.Rectangle((0, 0), 10, 10, linewidth=0, facecolor=quadrant_colors[1], alpha=0.3)
    ax.add_patch(rect1)
    
    # Quadrant 2: Left-Authoritarian (x: neg, y: pos)  
    rect2 = patches.Rectangle((-10, 0), 10, 10, linewidth=0, facecolor=quadrant_colors[2], alpha=0.3)
    ax.add_patch(rect2)
    
    # Quadrant 3: Left-Libertarian (x: neg, y: neg)
    rect3 = patches.Rectangle((-10, -10), 10, 10, linewidth=0, facecolor=quadrant_colors[3], alpha=0.3)
    ax.add_patch(rect3)
    
    # Quadrant 4: Right-Libertarian (x: pos, y: neg)
    rect4 = patches.Rectangle((0, -10), 10, 10, linewidth=0, facecolor=quadrant_colors[4], alpha=0.3)
    ax.add_patch(rect4)
    
    # Plot the axis lines
    ax.axhline(y=0, color='black', linewidth=2, alpha=0.8)  # Horizontal line
    ax.axvline(x=0, color='black', linewidth=2, alpha=0.8)  # Vertical line
    
    # Define colors for different religions/beliefs
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', 
              '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43',
              '#EE5A24', '#0984E3', '#6C5CE7', '#A29BFE', '#FD79A8']
    
    # Create scatter plot with different colors for each religion
    for idx, (i, row) in enumerate(df.iterrows()):
        ax.scatter(row['econ_score'], row['soc_score'], 
                  s=80, c=colors[idx % len(colors)], alpha=0.9, 
                  edgecolors='black', linewidth=1, zorder=5)
    
    # Add minimal labels for each point
    for idx, (i, row) in enumerate(df.iterrows()):
        religion_name = row['religion'].replace('_', ' ').title()
        
        # Smart label positioning to avoid overlap
        offset_x = 0.15
        offset_y = 0.15
        
        ax.annotate(religion_name, 
                   (row['econ_score'], row['soc_score']),
                   xytext=(offset_x, offset_y),
                   textcoords='offset points',
                   fontsize=8, fontweight='normal',
                   ha='left', va='bottom', zorder=6,
                   color='black')
    
    # Set plot limits and grid
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Labels and title
    ax.set_xlabel('Economic Left ← → Right', fontsize=12)
    ax.set_ylabel('Authoritarian ↑ ↓ Libertarian', fontsize=12)
    ax.set_title('Political Compass', fontsize=14, fontweight='bold')
    
    # Keep it clean - no scale markers
    
    # Tight layout and save
    plt.tight_layout()
    
    # Save the plot
    print(f"💾 Saving plot to: {output_file}")
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    
    # Show some statistics
    print(f"\n📊 Political Compass Statistics:")
    print(f"  Most Left (Economic): {df.loc[df['econ_score'].idxmin(), 'religion']} ({df['econ_score'].min()})")
    print(f"  Most Right (Economic): {df.loc[df['econ_score'].idxmax(), 'religion']} ({df['econ_score'].max()})")
    print(f"  Most Libertarian (Social): {df.loc[df['soc_score'].idxmin(), 'religion']} ({df['soc_score'].min()})")
    print(f"  Most Authoritarian (Social): {df.loc[df['soc_score'].idxmax(), 'religion']} ({df['soc_score'].max()})")
    
    # Quadrant analysis
    print(f"\n🗺️ Quadrant Analysis:")
    q1 = df[(df['econ_score'] > 0) & (df['soc_score'] > 0)]  # Right-Authoritarian
    q2 = df[(df['econ_score'] < 0) & (df['soc_score'] > 0)]  # Left-Authoritarian
    q3 = df[(df['econ_score'] < 0) & (df['soc_score'] < 0)]  # Left-Libertarian
    q4 = df[(df['econ_score'] > 0) & (df['soc_score'] < 0)]  # Right-Libertarian
    
    print(f"  Right-Authoritarian: {len(q1)} - {', '.join(q1['religion'].tolist())}")
    print(f"  Left-Authoritarian: {len(q2)} - {', '.join(q2['religion'].tolist())}")
    print(f"  Left-Libertarian: {len(q3)} - {', '.join(q3['religion'].tolist())}")
    print(f"  Right-Libertarian: {len(q4)} - {', '.join(q4['religion'].tolist())}")
    
    print(f"\n✅ Political compass plot created successfully!")
    
    try:
        plt.show()
    except Exception:
        print("📱 Plot display not available in terminal, but image saved successfully!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create a political compass plot from CSV data")
    parser.add_argument("-i", "--input", default="_pc_scores.csv", help="Input CSV file path")
    parser.add_argument("-o", "--output", default="political_compass.png", help="Output image file path")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"❌ Input file not found: {args.input}")
        return
    
    # Create the plot
    create_political_compass_plot(args.input, args.output)

if __name__ == "__main__":
    main()
