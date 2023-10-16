import json
import random
import time
import paho.mqtt.client as mqtt
import networkx as nx
from functools import partial



# MQTT Broker configurations
broker_address = "localhost"
broker_port = 1883
status_topic = "status_message"
action_topic = "action_message"



def create_grid_graph(grid_length, grid_width):
    G = nx.DiGraph()

    for i in range(grid_length):
        for j in range(grid_width):
            current_node = i * grid_width + j + 1

            # Add right neighbor
            if j < grid_width - 1:
                G.add_edge(current_node, current_node + 1)
                G.add_edge(current_node + 1, current_node)

            # Add bottom neighbor
            if i < grid_length - 1:
                G.add_edge(current_node, current_node + grid_width)
                G.add_edge(current_node + grid_width, current_node)

    return G

def find_shortest_path(graph, start_node, end_node):
    try:
        shortest_path = nx.algorithms.shortest_path(graph, source=start_node, target=end_node)
        return shortest_path
    except nx.NetworkXNoPath:
        return None
    
def update_path(robot_paths, grid_graph, order_nodes, current_node_list):
    
    for robot_id in robot_paths.keys():
        if (robot_paths[robot_id]['path'] == []) and (robot_paths[robot_id]['status'] == "readyToMove"):
            goal_node = random.choice(order_nodes)
            robot_paths[robot_id]['path'] = find_shortest_path(grid_graph, current_node_list[robot_id-1], int(goal_node))
            robot_paths[robot_id]['status'] = "movingToPick"
        if (len(robot_paths[robot_id]['path']) == 1):
            robot_paths[robot_id]['status'] = "readyToPick"
        if (robot_paths[robot_id]['picktime'] != -1) and (time.time() > robot_paths[robot_id]['picktime']):
            robot_paths[robot_id]['status'] = "pickCompleted"
            robot_paths[robot_id]['picktime'] = -1

def generate_status_message(robot_id, robot_paths, current_node_list, battery_percentage_list):
    if (robot_paths[robot_id]['status'] == "movingToPick"):
        current_node_list[robot_id-1] = robot_paths[robot_id]['path'].pop(0)
    if (robot_paths[robot_id]['status'] == "readyToPick"):
        if(len(robot_paths[robot_id]['path']) == 1):
            current_node_list[robot_id-1] = robot_paths[robot_id]['path'].pop(0)
        else:
            return {}
    current_node = current_node_list[robot_id-1]
    robot_state = robot_paths[robot_id]['status']
    signal_strength = random.randint(40, 100)
    if (random.randint(0, 100) > 70):
        battery_percentage_list[robot_id-1] -= 5
    battery_percentage = battery_percentage_list[robot_id-1]
    if (random.randint(0, 100) > 80):
        obstacle_status = True
    else:
        obstacle_status = False

    status_message = {
        "robot_id": robot_id,
        "current_node": current_node,
        "robot_state": robot_state,
        "signal_strength": signal_strength,
        "battery_percentage": battery_percentage,
        "obstacle_status": obstacle_status
    }

    if (robot_paths[robot_id]['status'] == "pickCompleted"):
        robot_paths[robot_id]['status'] = "readyToMove"

    print('robot: ', robot_id, ', node: ', current_node, ', state: ', robot_state, ', Signal: ', signal_strength, ', Battery: ', battery_percentage, ', Obstacle: ', obstacle_status)

    return json.dumps(status_message)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
        client.subscribe(action_topic)
    else:
        print("Failed to connect, return code: ", rc)

def on_publish(client, userdata, mid):
    
    print("Message published")

def on_message(client, userdata, message, robot_paths ):
    payload = message.payload.decode('utf-8')
    action_message = json.loads(payload)
    
    #An error coming here check once.
    robot_id = action_message['robot_id']
    order_id = action_message['order_id']
    item_id = action_message['item_id']
    quantity = action_message['quantity']
    print('Message received -', ' robot: ', robot_id, ', order: ',order_id, ', item: ', item_id, ', qty: ', quantity)
    if robot_paths[robot_id]['status'] == "readyToPick":
        robot_paths[robot_id]['picktime'] = time.time() + random.uniform(5, 10)
    else:
        print('Robot not at pick location: Wrong pick action requested')


if __name__ == "__main__":
    # Get Warehouse parameters and set Environment
    with open('parameters.json', 'r') as file:
        params_data = json.load(file)
    number_of_robots = params_data['number_of_robots']
    grid_length = params_data['grid_length']
    grid_width = params_data['grid_width']
    battery_percentage_list = [random.randint(40, 100) for _ in range(number_of_robots)]
    current_node_list = [random.randint(1, grid_length*grid_width) for node in range(number_of_robots)]
    grid_graph = create_grid_graph(grid_length, grid_width)
    robot_paths = {i+1: { "path": [], "status": "readyToMove", "picktime": -1} for i in range(number_of_robots)}

    # Get destination nodes
    with open('pick.json', 'r') as file:
        order_data = json.load(file)
    order_nodes = list(order_data.keys())

    on_message_with_extra = partial(on_message, robot_paths=robot_paths)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message_with_extra
    
    robot_id = 0

    try:
        client.connect(broker_address, broker_port)
        client.subscribe("server")
        client.loop_start()
        
        while True:
            update_path(robot_paths, grid_graph, order_nodes, current_node_list)

            #for robot_idx in robot_paths.keys():
            
            
            if (robot_paths[robot_id+1]['status'] == "pickCompleted"):
                data = {
                    'robot_id': robot_id+1
                }
                client.publish("pickAck", json.dumps(data))
            status_msg = generate_status_message(robot_id+1, robot_paths, current_node_list, battery_percentage_list)
            robot_id = (robot_id + 1) % number_of_robots
            
            if status_msg != {}:     
                client.publish(status_topic, status_msg)
            time.sleep(random.uniform(1/number_of_robots, 5/number_of_robots))

    except KeyboardInterrupt:
        print("Exiting...")
        client.loop_stop()
        client.disconnect()