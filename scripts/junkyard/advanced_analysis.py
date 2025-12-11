import sqlite3
import spacy
from collections import Counter
import networkx as nx
import json
import os

# Ensure spacy model is present
# python -m spacy download en_core_web_sm (usually handled by dependencies)
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

DB_PATH = "data/bible.db"

def get_corpus_text():
    conn = sqlite3.connect(DB_PATH)
    # Get ID and Content to track co-occurrence per paragraph
    rows = conn.execute("SELECT id, content FROM text_chunks").fetchall()
    conn.close()
    return rows

def extract_named_entities():
    print("Loading NER extraction...")
    rows = get_corpus_text()
    
    entity_counter = Counter()
    co_occurrences = Counter()
    
    # Process in chunks to be visibly actively
    print(f"Processing {len(rows)} paragraphs...")
    
    for row_id, text in rows:
        doc = nlp(text)
        
        # Extract Entities for this paragraph
        # We focus on PERSON, ORG, GPE (Location)
        ents = []
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                clean_name = ent.text.strip().replace("\n", " ").title()
                if len(clean_name) > 2:
                    ents.append(clean_name)
                    entity_counter[clean_name] += 1
        
        # Build Co-occurrence (Graph Edges)
        unique_ents = sorted(list(set(ents)))
        for i in range(len(unique_ents)):
            for j in range(i + 1, len(unique_ents)):
                edge = tuple(sorted([unique_ents[i], unique_ents[j]]))
                co_occurrences[edge] += 1
                
    return entity_counter, co_occurrences

def analyze_graph(entity_counter, co_occurrences):
    print("\n--- GRAPH CENTRALITY ANALYSIS ---")
    G = nx.Graph()
    
    # Add Nodes
    for ent, count in entity_counter.items():
        if count > 5: # Filter noise
            G.add_node(ent, weight=count)
            
    # Add Edges
    for (u, v), weight in co_occurrences.items():
        if u in G and v in G:
            G.add_edge(u, v, weight=weight)
            
    if len(G.nodes) == 0:
        print("No significant graph found.")
        return

    # 1. Degree Centrality (Who knows the most people?)
    degree = nx.degree_centrality(G)
    print("\nTop 10 Connected Characters (Degree Centrality):")
    for node, score in sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{node}: {score:.3f}")

    # 2. Betweenness Centrality (Who is the bridge between groups?)
    betweenness = nx.betweenness_centrality(G)
    print("\nTop 10 Bridge Characters (Betweenness Centrality):")
    for node, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{node}: {score:.3f}")
        
    # 3. Community Detection (Who hangs out with whom?)
    print("\n--- FACTION / GROUP DETECTION ---")
    try:
        communities = nx.community.louvain_communities(G, seed=42)
        for i, comm in enumerate(communities):
            members = sorted(list(comm), key=lambda x: entity_counter[x], reverse=True)
            if len(members) > 3: # Ignore tiny clusters
                top_members = members[:5]
                print(f"Cluster {i+1}: {', '.join(top_members)}")
    except AttributeError:
        # Fallback for older networkx
        print("Community detection requires newer networkx or scipy.")


if __name__ == "__main__":
    ents, edges = extract_named_entities()
    
    print("\n--- TOP 20 NER ENTITIES ---")
    for ent, count in ents.most_common(20):
        print(f"{ent}: {count}")
        
    analyze_graph(ents, edges)
