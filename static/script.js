client = new Paho.Client(location.hostname, 8080, "clientid");
//var client = new Paho.Client('broker.hivemq.com', 8000, 'andrew22');


client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;
client.connect({onSuccess:onConnect,onFailure:onFail});


let pickState = new Map();

function onConnect(){
  client.subscribe('status_message');
  client.subscribe('pickAck');
}
function onFail(errorMessage){
    console.log(errorMessage);
}
function onConnectionLost(responseObject){
    console.log("conection lost")
}
function onMessageArrived(message){
    if (message.destinationName == "status_message"){
        ready(message.payloadString)
    }
    //You dont need to listen to server
    else if(message.destinationName=="pickAck") {
        serverready(message.payloadString) 
    }
}

async function serverready(msg){
    data = JSON.parse(msg)
    if (pickState.has(data['robot_id'])){
        for (var i = 0; i < pickState.get(data['robot_id']).length; i++){
            var order_id = pickState.get(data['robot_id'])[i][2];
            var item_id =  pickState.get(data['robot_id'])[i][4];
            var location = pickState.get(data['robot_id'])[i][0];
            fetch("http://localhost:5000/pickConfirm", {
                    method: "POST",
                    body: JSON.stringify({
                        'location': location,
                        'confirmed_qty': pickState.get(data['robot_id'])[i][3],
                        'check_digit': pickState.get(data['robot_id'])[i][1],
                        'order_id': order_id
                        
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8"
                    }
                })
                .then((response) => response.json())
                .then((json) => {
                        console.log("Order"+order_id+item_id+location)
                        var li = document.getElementById("Order"+order_id+item_id+location);
                        li.remove();
                        for (var j = 0; j < pickState.get(data['robot_id']).length; j++){
                            if (pickState.get(data['robot_id'])[j][2] == order_id && pickState.get(data['robot_id'])[j][4] == item_id && pickState.get(data['robot_id'])[j][0] == location){
                                pickState.get(data['robot_id']).splice(j, 1);
                            }
                        }
                });
        }
    }
    
}


async function ready(msg){
    data = JSON.parse(msg)
    document.getElementById(data['robot_id']+"RobotS").innerText=data['signal_strength']
    document.getElementById(data['robot_id']+"RobotC").innerText=data['battery_percentage']

    //Removing previous position 
    var prevpos = document.getElementById(data['robot_id']+"prev")
    if (prevpos) {
        prevpos.remove();
    }

    currpos = document.getElementById(data['current_node']+"pos")
    var span = document.createElement('p');
    span.appendChild(document.createTextNode("Rob"+data['robot_id']))
    span.setAttribute("id", data['robot_id']+"prev")
    span.setAttribute("class", "Robdisplay")
    currpos.appendChild(span)
    //currpos.classList.add(data['robot_id']+"prev")
    //currpos.innerText = "Robot_"+data['robot_id']

    if (data['obstacle_status'] ==  true){
        span.innerText += "**";
    }

    //If status of the robot is readytoPick
    if (data['robot_state'] == 'readyToPick'){
            //robot_paths[robot_id]['status'] = "readyToPick" //Do I need this line
            const response = await fetch("http://localhost:5000/getPick/location="+data['current_node']);
            const res = await response.json();
            if (res['error'] == true){
                console.log(res['message'])
            }
            else {
                for (var i = 0; i < res['pick'].length; i++){
                    if (pickState.has(data['robot_id'])){
                        pickState.get(data['robot_id']).push([data['current_node'], res["pick"][i]['check_digit'], res['pick'][i]['order_id'], res['pick'][i]['quantity'], res['pick'][i]['item_id']])
                    }
                    else{
                        pickState.set(data['robot_id'],[[data['current_node'], res["pick"][i]['check_digit'], res['pick'][i]['order_id'], res['pick'][i]['quantity'], res['pick'][i]['item_id']]])
                    }

                    list = document.getElementById("tasks");
                    var li = document.createElement('li');
                    var text = "Order" + res['pick'][i]['order_id'] + ", Item" + res['pick'][i]['item_id'] +", Location " + data['current_node'] 
                    li.appendChild(document.createTextNode(text));
                    li.setAttribute("id", "Order"+res['pick'][i]['order_id']+res['pick'][i]['item_id']+data['current_node'])
                    list.appendChild(li);

                    //Robot_id, order_id, item_id and quantity - Needs to be published
                    body = {
                        'robot_id': data['robot_id'],
                        'order_id': res['pick'][i]['order_id'],
                        'item_id' : res['pick'][i]['item_id'],
                        'quantity': res['pick'][i]['quantity']
                    }
                    Message = new Paho.Message(JSON.stringify(body));
                    Message.destinationName = "server";
                    client.send(Message);
                }
            }
    }
}
