import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import collections
from collections import defaultdict


def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded file: {file_path}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Data shape: {df.shape}")
        print(f"First 5 rows:\n{df.head()}")
        return df
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def construct_network(df, page_col='page_name', thread_col='thread_subject', user_col='user_name'):

    G = nx.Graph()

    users = df[user_col].unique()
    user_to_id = {user: i for i, user in enumerate(users)}
    id_to_user = {i: user for i, user in enumerate(users)}

    for user_id in range(len(users)):
        G.add_node(user_id)

    additional_data = {
        'page_comments': defaultdict(list),
        'thread_comments': defaultdict(list),
        'user_comments': defaultdict(list),
        'page_users': defaultdict(set),
        'thread_users': defaultdict(lambda: defaultdict(set))
    }

    for _, row in df.iterrows():
        page = row[page_col]
        thread = row[thread_col]
        user = row[user_col]

        additional_data['page_comments'][page].append((user, thread))
        additional_data['thread_comments'][(page, thread)].append(user)
        additional_data['user_comments'][user].append((page, thread))
        additional_data['page_users'][page].add(user)
        additional_data['thread_users'][page][thread].add(user)

    edges_added = set()

    for page in additional_data['thread_users']:
        for thread in additional_data['thread_users'][page]:
            users_in_thread = list(additional_data['thread_users'][page][thread])

            if len(users_in_thread) > 1:
                for i in range(len(users_in_thread)):
                    for j in range(i + 1, len(users_in_thread)):
                        user1 = user_to_id[users_in_thread[i]]
                        user2 = user_to_id[users_in_thread[j]]

                        edge = tuple(sorted([user1, user2]))
                        if edge not in edges_added:
                            G.add_edge(user1, user2)
                            edges_added.add(edge)

    return G, user_to_id, id_to_user, additional_data


def analyze_network(G, network_name):

    print(f"\n===== {network_name} Analysis =====")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")


    components = list(nx.connected_components(G))
    print(f"Number of connected components: {len(components)}")

    largest_cc = max(components, key=len)
    print(f"Nodes in largest connected component: {len(largest_cc)}")

    largest_cc_subgraph = G.subgraph(largest_cc)

    try:
        diameter = nx.diameter(largest_cc_subgraph)
        print(f"Diameter of largest connected component: {diameter}")
    except nx.NetworkXError:
        print("Largest component is not connected or empty, cannot calculate diameter")

    degrees = [d for n, d in G.degree()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    print(f"Average degree: {avg_degree:.4f}")

    return components, largest_cc, degrees


def visualize_network(G, largest_cc, id_to_user, network_name, max_nodes=100):

    plt.figure(figsize=(12, 10))

    if len(G) > max_nodes:
        subgraph_nodes = list(largest_cc)[:max_nodes]
        subG = G.subgraph(subgraph_nodes)
        title = f"{network_name} - First {max_nodes} nodes of largest component"
    else:
        subG = G
        title = f"{network_name} Graph"

    pos = nx.spring_layout(subG, seed=42)

    node_degrees = dict(subG.degree())
    node_sizes = [20 + 5 * node_degrees[node] for node in subG.nodes()]

    nx.draw_networkx_nodes(subG, pos, node_size=node_sizes, node_color='skyblue', alpha=0.8)
    nx.draw_networkx_edges(subG, pos, width=0.5, alpha=0.5)

    if len(subG) <= 30:
        labels = {node: id_to_user[node] for node in subG.nodes()}
        nx.draw_networkx_labels(subG, pos, labels, font_size=8)

    plt.title(title)
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(f"{network_name.replace(' ', '_')}_network.png", dpi=300)
    plt.show()


def plot_degree_distribution(degrees, network_name):

    plt.figure(figsize=(10, 6))

    degree_count = collections.Counter(degrees)
    deg, cnt = zip(*sorted(degree_count.items()))

    plt.bar(deg, cnt, width=0.80, color="blue", alpha=0.7)
    plt.title(f"Degree Distribution of {network_name}")
    plt.ylabel("Frequency")
    plt.xlabel("Degree")
    plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{network_name.replace(' ', '_')}_degree_distribution.png", dpi=300)
    plt.show()


def check_cycles(G, network_name):

    print(f"\n===== Cycle Analysis for {network_name} =====")
    try:
        cycle = nx.find_cycle(G)
        print(f"Network contains cycles, e.g.: {cycle[:3]}")
        return True
    except nx.NetworkXNoCycle:
        print("Network is a tree (no cycles)")
        return False


def main():
    files = {
        "large": "C:/Users/13368/Desktop/network/coursework/datasets.zip/datasets/USERS.csv",
        "medium": "C:/Users/13368/Desktop/network/coursework/datasets.zip/datasets/WIKIPROJECTS.csv",
        "small": "C:/Users/13368/Desktop/network/coursework/datasets.zip/datasets/REQUEST_A_QUERY.csv"
    }

    for size, file_path in files.items():
        print(f"\n\n==========================")
        print(f"Starting analysis of {size} network: {file_path}")
        print(f"==========================")

        df = load_data(file_path)
        if df is None:
            print(f"Skipping analysis of {file_path}")
            continue

        print("Constructing network...")
        G, user_to_id, id_to_user, additional_data = construct_network(df,page_col='page_name', thread_col='thread_subject', user_col='username')

        print("Analyzing network...")
        analyze_network(G, f"{size.capitalize()} Network")

        print("Checking for cycles...")
        check_cycles(G, f"{size.capitalize()} Network")


        print(f"\nCompleted analysis of {size} network: {file_path}")


if __name__ == "__main__":
    main()