# Accio Robotics Full Stack Developer Task
This folder consists of the mock Server needed to make API calls for the smooth operations of the robot.

## Dependencies
These files need Flask-Python, Paho and Networkx to run so make sure you have it installed in your sytem

## How to run
Extract the zip file into your system
### Terminal 1
```
cd <path to api_server folder>
python3 server_emulator.py
```
> **Note:** Make sure you have the API server running before launching any other script 
### Terminal 2

```
cd <path to api_server folder>
python3 robot_emulator.py
```
> **Note: Make sure you have an MQTT broker running in the background**
## API
There are two API calls which you need to make

### GET
```
/getPick/location=<the node the robot is at>
```
You will make this call whenever the Robot status is **readyToPick**. Expect the following response codes

#### Code 200
The success code will have the following response
```
{
    "error": false,
    "error_code": 0,
    "message": "Success",
    "pick": []
}
```
Where pick will contain the picks you have to do at that particular location. A location can have more than 1 pick also so make sure you display all the picks at that location one by one. After each pick there should be an API call which will confirm that pick. So for example if there are 3 picks at a location, you need to make 3 API calls to confirm picks
#### Code 400
This error code will have the following response
```
{
    "error": true,
    "error_code": 1,
    "message": "Wrong Location provided"
}
```
This means that the location is not present in the grid
#### Code 401
This error code will have the following response
```
{
    "error": true,
    "error_code": 1,
    "message": "Wrong Input"
}
```
This means that the location input is not correct
### POST
```
/pickConfirm
```
This API is called whenever you want to confirm that the item at the location has been picked. The body of the POST call should be as follows:
```
{
    "location": <pick location>,
    "order_id": <order ID received from GET call>,
    "confirmed_qty": <how many items were picked>,
    "check_digit": <unique id received from GET call>
}
```
Fill the values based on the GET call you make when you get **readyToPick** from Robot.

#### Code 200
The success code will have the following response
```
{
    "confirmed_qty": <qty added by you>,
    "error": false,
    "error_code": 0,
    "message": "Success"
}
```
#### Code 400
This error code will have the following response
```
{
    "error": true,
    "error_code": 1,
    "message": "Wrong Location"
}
```
#### Code 401
This error code will have the following response
```
{
    "error": true,
    "error_code": 2,
    "message": "Wrong check_digit or order_id"
}
```

#Pip install requests