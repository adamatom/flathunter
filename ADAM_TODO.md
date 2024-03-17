# Adam TODO

[x] Add slack webhook, different than wohnung listing webhook
[x] return to headless chrome
[x] tailscale-ify the computer running the bot, allow remote captcha solving
[x] Send new listings to Telegram
[x] Allow for self-solving captcha, ask for help when captcha present
[x] Move all base captcha class code out of crawler ABC
[x] add Nelle's telegram
[x] check for updates
[x] extract json extractor out of crawler into new object
[x] Fix Unable to find IS24 variable in window - why do we see this error once?
[x] Why doesnt the bot try to solve captcha on startup?
[x] Reduce panicyness of bot detection
[x] Allow captcha solving from phone
[x] fix italian crawlers
[x] consider making _get_page_as_soup a standalone function
[ ] Use telegram to send requests for solutions
[ ] fix config captcha settings, where setting the debug port doesnt work and is hardcoded to 39999 in chrome_wrapper.py
[ ] replace blocking recaptcha on start-up if not using manual captcha solving
[ ] Implement optional login-in stage
[ ] Fix setup wizard
[ ] Implement form submitters for ImmoScout
[ ] Pretty-ify the messages to slack, the previous slack logger looked nicer
[ ] combine bot-machine and captcha-machine
[ ] Send listing to ChatGPT to generate customized application letter
[ ] put chrome driver settings back, see if that is causing zombie chrome processes
[ ] add proxy support to bots that use selenium. get proxy url, feed driver

## Get IDs of Telegram Accounts
Send a message to BerLabBot, then look for the ID here:
`curl https://api.telegram.org/bot6891352361:AAGQxTwwLSAj4c0I5zW891uYCHcvdaQStWE/getUpdates`


## Allow Desktop to Connect to Chrome Debug 

One Laptop (bot-machine) is running the bot python. Another Laptop (like at
work, or at home), connects to the Tailscale network and is able to connect to
the chrome debug port on bot-machine without any authentication.

Connect to Tailscale, ssh into bot-machine, and enable a Local port forward,
but running on the server. This overrides Chrome's desire to block remote
traffic to its debug port. Run this in a tmux or screen session.

```
ssh -L 0.0.0.0:9223:localhost:39999 localhost -N 
```

## Use Phone to VNC into captcha-machine

Another Laptop (captcha-machine) is connected to the Tailscale network and can
access the bot-machine's open Chrome debug port. Configure your phone/whatever
to create a Local port forward from 5901 to the captcha-machine:5901. This
allows the phone to connect to the captcha-machine's vnc server that is
configured to run while only accepting local connections.

on phone/vnc-viewer
`ssh -L 5901:localhost:5901 adam@captcha-machine -N`

Enable the port forwarding locally.

ssh from the phone into captcha-machine and run your vnc-server:
`x11vnc -localhost -display :1 -usepw -rfbport 5901`

connect the phone's vnc client to localhost:5901.


## Explanation of the SSH local port forwards

The primary difference between the two scenarios here lies in where
the local port forwarding is executed and which end of the connection is
considered the "local" side for the purpose of the port forwarding.

### Scenario 1: Server-Side Local Port Forwarding (SSH command run on the server)

* *Command Example*: `ssh -L 0.0.0.0:9223:localhost:39999 localhost -N`
* *Execution Location*: This command is run on the server.
* *Purpose*: This setup allows remote clients to connect to a service on the
    server that is only listening for local connections. By running
    this SSH command on the server and specifying 0.0.0.0 as the bind
    address, you make the forwarded port available on all network
    interfaces of the server, effectively allowing remote access to
    the service.
* *Flow*: Remote client → Server's port 9223 (open to all) → Forwarded through
    SSH tunnel to localhost:39999 (on the server itself).

### Scenario 2: Client-Side Local Port Forwarding (SSH command run on the client)

* *Command Example*: `ssh -L 5901:localhost:5901 user@server -N`
* *Execution Location*: This command is run on the client.
* *Purpose*: This setup enables the client to securely access a VNC service
    running on the server that is configured to accept only local connections.
    The VNC service listens on port 5901 but is not directly exposed to the
    internet for security reasons.
* *Flow*: VNC Client on localhost:5901 (on the client machine) → Forwarded
    through SSH tunnel to localhost:5901 (on the server).

### Key Differences:

Where the SSH Command Is Executed: In the first scenario, the SSH command
is executed on the server, with the goal of exposing a local service to
remote clients. In the second scenario, the SSH command is executed on the
client, aiming to access a remote service that is only available locally on
the server.

"Local" Context: In both cases, "localhost" refers to the machine on which
the forwarded service is running. However, where the forwarding is
initiated changes the perspective of "local":

In scenario 1, the server forwards from its own external interface back to itself.
In scenario 2, the client forwards from itself to a service on the server.
