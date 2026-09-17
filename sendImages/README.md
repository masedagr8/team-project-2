# Image Transmission

## Note

**Run `rebel_server.py` first.**

### To run `rebel_server.py`

```bash
python rebel_server.py
```

Then run:

```bash
python send_images.py --file ./Target.zip --server YOUR_LAPTOP_IP
```

### To run `send_images.py`

First run the image sorter:

```bash
python ImageSorter.py --top 10
```

Then run:

```bash
python send_images.py --file ./Target.zip --server 192.168.1.100
```

Where `192.168.1.100` is the IP address of the laptop.

## Expected Output

If everything is working, the output should look like:

```text
Rebel server listening on port 5000...
Connection from ('192.168.x.x', ...)
Receiving Target.zip (123456 bytes)...
Received 123456/123456 bytes
Saved to received/Target.zip
```

## TODO

- Change the normal TCP portion to use radio.

